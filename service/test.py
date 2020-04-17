a = "Whole Foods Market Subtotal (5 items)"


b = ""

for i in range(len(a)):
    if (b != "Whole Foods"):
        b += a[i]


print(b)