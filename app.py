from flask import Flask, request
from flask_restful import Api, Resource, reqparse
import psycopg2
import africastalking

app = Flask(__name__)
api = Api(app)

# Database connection
conn = psycopg2.connect(
    dbname='your_database_name',
    user='your_database_user',
    password='your_database_password',
    host='localhost'
)

# Initialize Africa's Talking
africastalking.initialize(username='YOUR_USERNAME', api_key='YOUR_API_KEY')


class CustomerResource(Resource):
    def get(self, customer_id):
        # Retrieve customer details from database
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        if customer:
            return {'id': customer[0], 'name': customer[1], 'code': customer[2]}, 200
        else:
            return {'message': 'Customer not found'}, 404

    def post(self):
        # Add a new customer to the database
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Name is required')
        parser.add_argument('code', type=str, required=True, help='Code is required')
        args = parser.parse_args()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, code) VALUES (%s, %s) RETURNING id", (args['name'], args['code']))
        new_customer_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {'message': 'Customer created', 'id': new_customer_id}, 201


class OrderResource(Resource):
    def post(self):
        # Add a new order to the database
        parser = reqparse.RequestParser()
        parser.add_argument('customer_id', type=int, required=True, help='Customer ID is required')
        parser.add_argument('item', type=str, required=True, help='Item is required')
        parser.add_argument('amount', type=float, required=True, help='Amount is required')
        parser.add_argument('time', type=str, required=True, help='Time is required')
        args = parser.parse_args()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (customer_id, item, amount, time) VALUES (%s, %s, %s, %s)",
                       (args['customer_id'], args['item'], args['amount'], args['time']))
        conn.commit()
        cursor.close()
        # Send SMS alert to customer
        send_sms_alert(args['customer_id'], args['item'], args['amount'])
        return {'message': 'Order created'}, 201


def send_sms_alert(customer_id, item, amount):
    # Retrieve customer's phone number from database
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM customers WHERE id = %s", (customer_id,))
    customer_code = cursor.fetchone()[0]
    cursor.close()
    # Assuming customer_code contains the phone number
    customer_phone = '+' + customer_code
    message = f'New order placed: {item} - Amount: {amount}'
    # Send SMS
    sms = africastalking.SMS
    sms.send(message, [customer_phone])


api.add_resource(CustomerResource, '/customer', '/customer/<int:customer_id>')
api.add_resource(OrderResource, '/order')

if __name__ == '__main__':
    app.run(debug=True)
