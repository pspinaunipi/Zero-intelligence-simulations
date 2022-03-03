import unittest
import numpy
import sys, os
sys.path.append("../")
from fast_limit_order import *

class TestSantaFe(unittest.TestCase):

    def test_find_min(self):
        a = np.array([99,15,68,4,88,33,4,7,88,4])
        b = [18,45,86,44,34,67,9,78,9]
        self.assertEqual(find_min(a),(4,3))
        self.assertEqual(find_min(b),(9,6))

    def test_find_max(self):
        a = np.array([15,68,4,88,33,4,7,88,4])
        b = [18,45,86,44,34,67,9,86,9]
        self.assertEqual(find_max(a),(88,3))
        self.assertEqual(find_max(b),(86,2))

    def test_out_of_equilibrium_start(self):

        b_orders, s_orders = out_of_equilibrium_start(2,20,1)
        self.assertEqual(b_orders,[i for i in range(2,12)])
        self.assertEqual(s_orders,[i for i in range(12,21)])

        b_orders, s_orders = out_of_equilibrium_start(1,20,1)
        self.assertEqual(b_orders,[i for i in range(1,11)])
        self.assertEqual(s_orders,[i for i in range(11,21)])

        b_orders, s_orders = out_of_equilibrium_start(0,20,5)
        self.assertEqual(b_orders,[0,5,10])
        self.assertEqual(s_orders,[15,20])

    def test_next_order(self):

        buy_l  = [1.2, 1.8, 1.9 , 5.]
        sell_l = [1.7, 56., 1.3, 4.]
        buy_c  = [45., 35.]
        sell_c = [1.5, 2. , 6. , 0.5]
        mo     = 12.

        t_time, pos, sign, limit, market, cancel = next_order(buy_l, sell_l, buy_c, sell_c, mo)

        self.assertEqual(t_time, 0.5)
        self.assertEqual(pos, 3)
        self.assertEqual(sign, -1)
        self.assertEqual(limit, False)
        self.assertEqual(cancel, True)
        self.assertEqual(market, False)

        buy_c  = [45., 0.35]
        t_time, pos, sign, limit, market, cancel = next_order(buy_l, sell_l, buy_c, sell_c, mo)

        self.assertEqual(t_time, 0.35)
        self.assertEqual(pos, 1)
        self.assertEqual(sign, 1)
        self.assertEqual(limit, False)
        self.assertEqual(cancel, True)
        self.assertEqual(market, False)

        mo = 0.02

        t_time, pos, sign, limit, market, cancel = next_order(buy_l, sell_l, buy_c, sell_c, mo)

        self.assertEqual(t_time, 0.02)
        self.assertEqual(pos, 0)
        self.assertEqual(limit, False)
        self.assertEqual(cancel, False)
        self.assertEqual(market, True)

        buy_l  = [0.01, 1.2, 1.8, 1.9 , 5.]

        t_time, pos, sign, limit, market, cancel = next_order(buy_l, sell_l, buy_c, sell_c, mo)

        self.assertEqual(t_time, 0.01)
        self.assertEqual(pos, 0)
        self.assertEqual(sign, 1)
        self.assertEqual(limit, True)
        self.assertEqual(cancel, False)
        self.assertEqual(market, False)

        sell_l = [1.7, 56., 1.3, 4., 0.0001]

        t_time, pos, sign, limit, market, cancel = next_order(buy_l, sell_l, buy_c, sell_c, mo)

        self.assertEqual(t_time, 0.0001)
        self.assertEqual(pos, 4)
        self.assertEqual(sign, -1)
        self.assertEqual(limit, True)
        self.assertEqual(cancel, False)
        self.assertEqual(market, False)

    def test_subtract_from_list(self):
        lst = [1,4,6,2,1,5]
        new_lst = subtract_from_list(lst,1)
        self.assertEqual(lst,[0,3,5,1,0,4])

    def test_best_prices(self):
        a = [44,56,23,45,23,56]
        self.assertEqual(find_best_prices(1,a),2)
        self.assertEqual(find_best_prices(-1,a),1)



if __name__ == "__main__":
    unittest.main()
