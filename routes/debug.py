from flask import Blueprint, jsonify
from models import Card, Pack

bp = Blueprint('debug', __name__)

@bp.route('/debug/cards')
def debug_cards():
    """Debug endpoint to list all cards and their properties"""
    cards = Card.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'rarity': c.rarity,
        'is_prime': c.is_prime,
        'image': c.image is not None,
        'created_at': c.created_at.isoformat() if c.created_at else None
    } for c in cards])

@bp.route('/debug/packs')
def debug_packs():
    """Debug endpoint to list all packs and their properties"""
    packs = Pack.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'cards_count': p.cards_count,
        'min_rarity': p.min_rarity,
        'max_rarity': p.max_rarity,
        'prime_chance': p.prime_chance,
        'is_active': p.is_active,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in packs])
