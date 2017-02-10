from __future__ import print_function
from kafka import KafkaProducer
import json
import time


class EventadorProducer():
    def __init__(self, brokers, topic):
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=brokers,
                                      key_serializer=str.encode,
                                      value_serializer=lambda m: json.dumps(m))

    def send_one(self, key, datum):
        self.producer.send(self.topic, key, datum)
        self.flush()
        self.log_time()

    def send_all(self, key, data):
        [self.producer.send(self.topic, key=key, value=datum) for datum in data]
        self.log_topic()
        # This is a blocking call
        self.flush()
        self.log_time()

    def ack_completion(self, asyncSend):
        record_metadata = asyncSend.get(timeout=10)
        return record_metadata.topic, record_metadata.partition, record_metadata.offset


    def flush(self):
        self.producer.flush()

    def log_time(self):
        localtime = time.localtime()
        htime = time.strftime("%Y/%m/%d-%H%:%M%:%S", localtime)
        print("Finished producing at {}\n".format(htime))

    def log_topic(self):
        print("\nProducing data to Eventador topic: " + self.topic)