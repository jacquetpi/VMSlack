import vowpalwabbit
import numpy as np
import math
from sklearn import datasets
from sklearn.model_selection import train_test_split
from vowpalwabbit.sklearn import (
    VW,
    VWClassifier,
    VWRegressor,
    tovw,
    VWMultiClassifier,
    VWRegressor,
)

class Predictor(object):
    """
    A Predictor is in charge to predict the next active resources
    ...


    Public Methods
    -------
    iterate()
        Deploy a VM to the appropriate CPU subset    
    """
    def __init__(self, **kwargs):
        pass
    
    def predict(self):
        raise ValueError('Not implemented')


class PredictorCsoaa(Predictor):
    """
    This class use a CSOAA: Cost-Sensitive One Against All classifier to predict next active resources
    https://github.com/VowpalWabbit/vowpal_wabbit/wiki/Cost-Sensitive-One-Against-All-%28csoaa%29-multi-class-example
    ...
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        additional_attributes = ['monitoring_window', 'monitoring_learning', 'monitoring_leeway']
        for req_attribute in additional_attributes:
            if req_attribute not in kwargs: raise ValueError('Missing required argument', additional_attributes)
            setattr(self, req_attribute, kwargs[req_attribute])
        self.model_records = dict()
        self.last_features = None
        # Buffer attributes
        self.buffer_timestamp = None
        self.buffer_records = list()
        self.last_prediction = None

    def predict(self, timestamp : int, current_resources : int, metric : int):
        # Adapted from SmartHarvest https://dl.acm.org/doi/pdf/10.1145/3447786.3456225
        # Unlike them, we manage a dynamic set of cores (i.e. list of usable resources in our subset )

        if self.buffer_timestamp is None: self.buffer_timestamp = timestamp
        self.buffer_records.append(metric)

        # Tests
        first_call  = False
        safeguard   = False
        buffer_full = False
        if self.last_prediction is None: first_call = True
        if (not first_call) and (math.ceil(metric) == self.last_prediction): safeguard = True 
        if (not first_call) and ((timestamp - self.buffer_timestamp) >= self.monitoring_learning): buffer_full = True

        if first_call:
            self.last_prediction = current_resources
            return current_resources

        if (not safeguard) and (not buffer_full):
            return self.last_prediction

        if safeguard:
            self.last_prediction = current_resources
            return current_resources
        else:
            prediction = self.predict_on_new_model(timestamp=timestamp, current_resources=current_resources, metrics=self.buffer_records)
            self.buffer_timestamp = None
            self.buffer_records = list()
            self.last_prediction = prediction
            return prediction

    def predict_on_new_model(self, timestamp : int, current_resources : int, metrics : list):
        # Adapted from SmartHarvest https://dl.acm.org/doi/pdf/10.1145/3447786.3456225
        # Unlike them, we manage a dynamic set of cores (i.e. list of usable resources in our subset )
        
        # First, register peak associated to last iteration features
        if self.last_features is not None:
            self.add_record(timestamp=timestamp, peak_usage=max(metrics), features=self.last_features)
        #print('|_>: peak observed', max(metrics))

        # Safeguard on empty subsets
        if current_resources<=0: return current_resources

        # Generate current features
        current_features = self.__generate_features(metrics=metrics)
        self.last_features = current_features

        # Second, update model
        vw = vowpalwabbit.Workspace(csoaa=current_resources, quiet=True)
        raw_data = self.__generate_data_from_records(resources_count=current_resources)
        for data in raw_data: vw.learn(data)

        # Third, predict next peak based on model
        prediction = vw.predict('| ' + current_features)
        #print('New prediction:', prediction)
        vw.finish()
        return prediction

    def __generate_data_from_records(self, resources_count : int):
        data = list()
        for record_tuple in self.model_records.values():
            (peak_usage, features) = record_tuple
            label = self.__generate_labels_with_costs(resources_count=resources_count, observed_peak=peak_usage)
            data.append(label + ' | ' + features)
        return data

    def __generate_labels_with_costs(self, resources_count : int, observed_peak : float):
        negative_penalty_start = math.ceil(resources_count/2)
        costs = ''
        actual_peak_rounded = math.ceil(observed_peak)
        for core in range(1, resources_count+1):
            delta = np.abs(core-actual_peak_rounded)
            associated_cost = negative_penalty_start + delta if (core < actual_peak_rounded) else delta
            costs+= str(core) + ':' + str(float(associated_cost)) + ' '
        return costs[:-1]

    # TODO: add features based on new VM, new CPU count?
    def __generate_features(self, metrics : list):
        """Get CSOAA features as a string
        ----------

        Parameters
        ----------
        metrics : list
            List of usage resources to use to generate the feature

        Returns
        -------
        Features : str
            Features as string
        """
        return 'min:' + str(min(metrics)) + ' max:' + str(max(metrics)) +\
            ' avg:' + str(np.mean(metrics)) +  ' std:' + str(np.std(metrics)) + ' med:' + str(np.median(metrics))

    def add_record(self, timestamp : int, peak_usage : float, features : str):
        """Add new records to the collection attributes and manage expired data
        ----------

        Parameters
        ----------
        timestamp : int
            The timestamp key
        peak_usage : float
            Peak observed in this timestamp identified window
        features : str
            The last generated features
        """
        self.model_records[timestamp] = (peak_usage, features)
        self.remove_expired_keys(timestamp=timestamp, considered_dict=self.model_records)

    def remove_expired_keys(self, timestamp : int, considered_dict : dict):
        """Parse a dict where the key is a timestamp and remove all values being older than
        timestamp - self.MONITORING_WINDOW
        ----------

        Parameters
        ----------
        timestamp : int
            The timestamp key
        considered_dict : dict
            Dict to filter
        """
        records_to_remove = list()
        for record_timestamp in considered_dict.keys():
            if record_timestamp < (timestamp - self.monitoring_window): records_to_remove.append(record_timestamp)
        for record_to_remove in records_to_remove: del considered_dict[record_to_remove]

class PredictorMaxVMPeak(Predictor):

    def predict(self):
        #TODO: to fix
        res_needed_count = 0
        threshold_cpu    = 0
        for consumer in self.consumer_list:
            if threshold_cpu < consumer.get_cpu(): threshold_cpu = consumer.get_cpu() 
            if (consumer.get_uuid() not in self.hist_consumers_usage or len(self.hist_consumers_usage[consumer.get_uuid()]) < self.MONITORING_MIN):
                res_needed_count+= consumer.get_cpu() # not enough data
            # else:
            #     consumer_records  = [value for __, value in self.hist_consumers_usage[consumer.get_uuid()]]
            #     consumer_max_peak = consumer.get_cpu() * max(consumer_records) + self.MONITORING_LEEWAY*np.std(consumer_records)
            #     if consumer.get_cpu() < consumer_max_peak: consumer_max_peak = consumer.get_cpu()
            
            # res_needed_count += consumer_max_peak

        # Compute next peak
        subset_records  = [value for __, value in self.hist_usage]
        usage_current   = subset_records[-1] if subset_records else None
        usage_predicted = math.ceil(max(subset_records) + self.MONITORING_LEEWAY*np.std(subset_records)) if len(subset_records) >= self.MONITORING_MIN else len(self.get_res())

        # Watchdog, was our last prediction too pessimistic?
        if usage_current is not None and (math.ceil(usage_current) == len(self.active_res)): 
            print('#DEBUG: watchdog')
            usage_predicted = len(self.get_res())
        else:
            print('#DEBUG: no-watchdog')
        # Watchdog, do not overcommit a VM with itself
        if usage_predicted < threshold_cpu: usage_predicted = threshold_cpu
        # Watchdog, is there new VMs?
        if usage_predicted < res_needed_count: usage_predicted = res_needed_count

if __name__ == '__main__':
    # Test environment, to be removed
    num_classes = 4
    vw = vowpalwabbit.Workspace(csoaa=num_classes, quiet=True)
    raw_data = [
        "1:0.0 2:1.0 3:1.0 4:1.0 | a:0 b:1 c:1",
        "1:2.0 2:0.0 3:2.0 4:2.0 | b:1 c:1 d:1",
        "1:0.0 2:1.0 3:1.0 4:1.0 | a:8 c:1 e:1",
        "1:1.0 2:1.0 3:1.0 4:0.0 | b:1 d:1 f:1",
        "1:1.0 2:2.0 3:0.0 4:1.0 | d:1 e:1 f:1"
    ]
    for data in raw_data: 
        print(data)
        vw.learn(data)
    #model.fit(raw_data)
    prediction = vw.predict('| b:1 c:1 d:1')
    print(prediction)
    vw.finish()