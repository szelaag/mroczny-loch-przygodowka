from items import create_item
miecz = create_item("miecz")
print(miecz.attacks)                    # [Attack('light',4,6,0.0), Attack('heavy',10,16,0.4), Attack('stab',7,10,0.0)]
print(len(miecz.attacks))               # 3
print(create_item("noz").attacks)       # [] (fallback bez akcji)
print(create_item("klucz").attacks)     # [] (nie-broń)

