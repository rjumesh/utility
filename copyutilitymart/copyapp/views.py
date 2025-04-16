from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from copyapp.models import Contact, Product, Orders, OrderUpdate
from math import ceil
from django.views.decorators.csrf import csrf_exempt
import requests
import hashlib
import json

# Create your views here.
def index(request):
    allprods = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nslider = n // 4 + ceil((n / 4) - (n // 4))
        allprods.append([prod, range(1, nslider), nslider])
        
    params = {'allprods': allprods}
    return render(request, 'test/index.html', params)


def contact(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        email = request.POST.get("email")
        desc = request.POST.get("desc")
        pnumber = request.POST.get("phonenumber")
        myquery = Contact(name=name, email=email, desc=desc, phonenumber=pnumber)
        myquery.save()
        messages.info(request, 'We will get back to you soon.')
    return render(request, 'test/contact.html')


def about(request):
    return render(request, 'test/about.html')


def checkout(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to continue.')
        return redirect('login')

    if request.method == 'POST':
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amt', '')  # Changed from 'amount' to 'amt'
        email = request.user.email  # Use authenticated user's email
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        if amount:
            # First convert to float, then to int to handle decimal amounts
            amount = int(float(amount))

        # Save the order details in the database
        order = Orders(
            items_json=items_json,
            name=name,
            email=email,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            amount=amount
        )
        order.save()

        # Update the order status
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()

        thank = True

        # CASHFREE INTEGRATION
        order_id = str(order.order_id)
        customer_name = name
        customer_email = email
        customer_phone = phone
        order_amount = str(amount)
        return_url = "http://127.0.0.1:8000/callback/"  # URL to handle Cashfree response

        # Prepare Request Data
        payload = {
            # "appId": "",  # Replace with your Cashfree App ID
            "orderId": order_id,
            "orderAmount": order_amount,
            "orderCurrency": "INR",
            "customerName": customer_name,
            "customerEmail": customer_email,
            "customerPhone": customer_phone,
            "returnUrl": return_url
        }

        # # Generate Signature
        # def generate_signature(data, ):
        #     data_str = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
        #     data_str += f"&{}"
        #     return hashlib.sha256(data_str.encode()).hexdigest()

        

        # Send POST Request to Cashfree 
        url = "https://test.cashfree.com/v2/cftoken/order"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            cftoken = response_data.get("cftoken")

            # Redirect to Cashfree payment page
            # Add JavaScript to clear cart
            clear_cart_script = """
            <script>
                localStorage.removeItem('cart');
                window.location.href = '/';
            </script>
            """
            return HttpResponse(clear_cart_script)
        else:
            messages.error(request, "Failed to initiate payment. Please try again.")
            return redirect('/')

    return render(request, 'test/checkout.html')


@csrf_exempt
def callback(request):
    """Handle payment response from Cashfree."""
    if request.method == "POST":
        # Extract POST data
        data = request.POST
        order_id = data.get("orderId")
        order_amount = data.get("orderAmount")
        reference_id = data.get("referenceId")
        tx_status = data.get("txStatus")
        payment_mode = data.get("paymentMode")
        tx_msg = data.get("txMsg")
        tx_time = data.get("txTime")
        signature = data.get("signature")

        # Verify Signature
        def generate_signature(data, secret_key):
            data_str = "&".join(f"{k}={v}" for k, v in sorted(data.items()) if v)
            data_str += f"&{secret_key}"
            return hashlib.sha256(data_str.encode()).hexdigest()

        seret_ke = ""  # Replace with your Cashfree Se
        expected_signature = generate_signature({
            "orderId": order_id,
            "orderAmount": order_amount,
            "referenceId": reference_id,
            "txStatus": tx_status,
            "paymentMode": payment_mode,
            "txMsg": tx_msg,
            "txTime": tx_time
        }, seret_ke)

        if signature == expected_signature:
            if tx_status == "SUCCESS":
                # Update the order status in the database
                filter2 = Orders.objects.filter(order_id=order_id)
                for post1 in filter2:
                    post1.paymentstatus = "PAID"
                    post1.amountpaid = order_amount
                    post1.save()

                messages.success(request, "Order placed successfully! Payment completed.")
                return redirect('/')
            else:
                messages.error(request, "Payment failed! Please try again.")
                return redirect('/')
        else:
            messages.error(request, "Invalid payment signature! Please contact support.")
            return redirect('/')


def profile(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to continue')
        return redirect('auth/login')
    
    # Get orders for the current user
    current_user = request.user
    print(f"Debug - Current user: {current_user.username}, Email: {current_user.email}")
    
    # Try to find orders by both email and username
    orders = Orders.objects.filter(email__in=[current_user.email, current_user.username])
    print(f"Debug - Found {orders.count()} orders")
    
    # Print all orders for debugging
    for order in orders:
        print(f"Debug - Order ID: {order.order_id}, Email: {order.email}, Amount: {order.amount}")
    
    # Create a dictionary to store order details with their status updates
    orders_with_status = []
    for order in orders:
        order_dict = {
            'order': order,
            'status': None,
            'items': []
        }
        
        # Parse items_json to get product details
        if order.items_json:
            try:
                items = json.loads(order.items_json)
                order_dict['items'] = items
                print(f"Debug - Parsed items for order {order.order_id}: {items}")
            except json.JSONDecodeError as e:
                print(f"Debug - Error parsing items_json for order {order.order_id}: {e}")
                order_dict['items'] = []
        
        # Get the latest status update for this order
        if order.order_id:
            try:
                latest_status = OrderUpdate.objects.filter(
                    order_id=order.order_id
                ).order_by('-timestamp').first()
                order_dict['status'] = latest_status
                if latest_status:
                    print(f"Debug - Found status for order {order.order_id}: {latest_status.update_desc}")
            except OrderUpdate.DoesNotExist:
                print(f"Debug - No status found for order {order.order_id}")
        
        orders_with_status.append(order_dict)
    
    context = {'orders': orders_with_status}
    return render(request, 'test/profile.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'test/product_detail.html', {'product': product})



