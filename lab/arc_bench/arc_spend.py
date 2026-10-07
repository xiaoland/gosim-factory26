"""Estimate ARC transport usage, never supplier plans or the platform bill."""


def estimate(usage, prices):
    # Pi input excludes cache tokens; output already includes reasoning.
    # Keep the established usage_budget arithmetic without its ZIP downloader.
    total, known, missing = 0, 0, []
    for item in (usage or {}).get('items', []):
        model = item.get('model')
        rates = prices.get('rates', {}).get(model, {})
        tokens = item.get('tokens', {})
        for field in ('input', 'output', 'cacheRead', 'cacheWrite'):
            quantity = tokens.get(field)
            price = rates.get(field)
            if quantity == 0:
                known += 1
            elif isinstance(quantity, (int, float)) and not isinstance(quantity, bool) and quantity > 0 and price is not None:
                total += quantity * price / 1_000_000
                known += 1
            else:
                missing.append({'model': model, 'session_id': item.get('session_id'),
                                'field': field, 'tokens': quantity,
                                'reason': 'usage-missing' if quantity is None else 'price-missing'})
    complete = known and not missing and (usage or {}).get('status') == 'complete'
    return {'kind': 'estimate' if known else 'unknown',
            'status': 'observed-usage-subtotal' if known else 'no-priced-usage',
            'value': total if known else None, 'amount': total if known else None,
            'currency': prices['currency'],
            'coverage': 'complete' if complete else 'partial' if known else 'unknown',
            'missing': missing, 'price_source': prices['source'],
            'price_as_of': prices['observed_at'], 'usage_as_of': (usage or {}).get('as_of'),
            'as_of': (usage or {}).get('as_of'),
            'note': 'Known subtotal only; in-flight/unrecorded usage and unpriced components are not zero.'}
