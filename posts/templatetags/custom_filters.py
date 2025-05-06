from django import template

register = template.Library()


@register.filter
def sentiment_label(value):
    sentiment_map = {
        0: "Very Negative",
        1: "Negative",
        2: "Neutral",
        3: "Positive",
        4: "Very Positive",
    }
    return sentiment_map.get(value, "Unknown")
