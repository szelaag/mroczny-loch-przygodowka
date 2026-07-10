from items import create_item
miecz = create_item("miecz")
print(miecz.attacks)                    # [Attack('light',4,6,0.0), Attack('heavy',10,16,0.4), Attack('stab',7,10,0.0)]
print(len(miecz.attacks))               # 3
print(create_item("noz").attacks)       # [] (fallback bez akcji)
print(create_item("klucz").attacks)     # [] (nie-broń)

from items import create_item
m1 = create_item("miecz")
m2 = create_item("miecz")
print(m1.attacks is m2.attacks)    # True = współdzielona lista (problem przy mutacji akcji), False = osobna