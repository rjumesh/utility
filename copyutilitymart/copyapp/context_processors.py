def cart_total(request):
    cart = request.session.get('cart', {})
    total_items = sum(cart.values())
    return {'cart_total': total_items} 