from django import template

from horses.models import Horse, Inquiry

register = template.Library()


@register.simple_tag
def dashboard_stats():
    total_horses = Horse.objects.count()
    available_for_sale = Horse.objects.filter(
        is_for_sale=True,
        is_sold=False,
    ).count()
    sold_horses = Horse.objects.filter(is_sold=True).count()
    total_inquiries = Inquiry.objects.count()
    uncontacted_inquiries = Inquiry.objects.filter(is_contacted=False).count()

    return {
        "total_horses": total_horses,
        "available_for_sale": available_for_sale,
        "sold_horses": sold_horses,
        "total_inquiries": total_inquiries,
        "uncontacted_inquiries": uncontacted_inquiries,
    }
