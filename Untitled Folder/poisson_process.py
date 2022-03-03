import random


def poisson_generator(rate):
    arrival_time = random.expovariate(rate)
    return arrival_time

def lul(rate_limit,rate_market,rate_cancel,max_iterations=10):

    next_limit_order  = poisson_generator(rate_limit)
    next_market_order = poisson_generator(rate_market)
    next_cancel_order = poisson_generator(rate_cancel)

    for i in range(max_iterations):

        if next_limit_order < next_market_order and next_limit_order < next_cancel_order:
            #rescale times
            next_market_order -= next_limit_order
            next_cancel_order -= next_limit_order
            #generate time new limit order
            next_limit_order   = poisson_generator(rate_limit)

        elif next_market_order < next_limit_order and next_market_order < next_cancel_order:
            #rescale times
            next_limit_order  -= next_market_order
            next_cancel_order -= next_market_order
            #generate time new market order
            next_market_order   = poisson_generator(rate_market)

        elif next_cancel_order < next_limit_order and next_cancel_order < next_market_order:
            #rescale times
            next_limit_order  -= next_cancel_order
            next_market_order -= next_cancel_order
            #generate time new market order
            next_cancel_order   = poisson_generator(rate_cancel)




lul(0.30,0.20,0.10)
