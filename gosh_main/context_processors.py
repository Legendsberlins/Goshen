def cart_count(request):
    cart = request.session.get('cart', {})
    total_items = 0

    if isinstance(cart, dict):
        for qty in cart.values():
            try:
                total_items += int(qty)
            except (TypeError, ValueError):
                continue

    return {'cart_count': total_items}
