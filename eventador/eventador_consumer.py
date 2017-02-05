from __future__ import print_function
from kafka import KafkaConsumer
from config import s3conn
from config import esconn
from elasticsearch import helpers
import json
import uuid


class BaseEventadorConsumer(object):
    def __init__(self, config):
        self.config = config
        self.consumer = KafkaConsumer(bootstrap_servers=self.config['brokers'],
                                      value_deserializer=lambda s: json.loads(s, encoding='utf-8'),
                                      group_id=uuid.uuid4())

    def subscribe(self):
        self.consumer.subscribe(self.config['topic'])

    def poll(self):
        self.consumer.poll(max_records=self.config['max_records'])

    def collect(self, key):
        self.subscribe()
        self.poll()

        collected = 0
        data = []
        for msg in self.consumer:
            collected += 1

            if msg.key == key:
                data.append(msg.value)

            if collected >= self.config['max_records']:
                break

        self.close()
        return data

    def close(self):
        self.consumer.close()


# Can create additional publishers that inherit from BaseEventador consumer need a publish method and a collect method
class S3Publisher(BaseEventadorConsumer):
    def __init__(self, config):
        super(self.__class__, self).__init__(config)

    def publish(self, key):
        try:
            data = json.dumps(self.collect(key))

            bucket = self.config['bucket']
            s3conn.write_file_to_s3(data, key, bucket)

            print('{} written to {} bucket'.format(key, bucket))
        except Exception as ex:
            print(str(ex))



class ElasticSearchPublisher(BaseEventadorConsumer):
    def __init__(self, config):
        super(self.__class__, self).__init__(config)

    def publish(self, key):
        def docs_gen(docs):
            for doc in docs:
                index_dict = {
                    '_index': self.config['index'],
                    '_type': self.config['doc_type'],
                    '_source': doc
                }
                yield index_dict

        try:
            docs = self.collect(key)
            print("{} messages collected".format(len(docs)))

            es = esconn.esconn()
            helpers.bulk(es, docs_gen(docs), stats_only=True)
        except Exception as ex:
            print(str(ex))
