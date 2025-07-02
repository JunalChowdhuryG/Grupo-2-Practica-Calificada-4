from kafka import KafkaProducer
import sys

producer = KafkaProducer(bootstrap_servers='kafka:9092')
message = sys.argv[1] if len(sys.argv) > 1 else 'Hello, Kafka!'

producer.send('notifications', value=message.encode('utf-8'))

producer.flush()

print(f"Message sent: {message}")


