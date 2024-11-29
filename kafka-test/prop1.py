from kafka import KafkaConsumer

if __name__ == '__main__':
  consumer = KafkaConsumer('my_favorite_topic')
  for msg in consumer:
    print(msg)
