total = 0

for i in range(3):  # 第 1 層縮排開始
    print(f"外層第 {i} 圈")  # ← 縮排 1 層，屬於外層 for

    for j in range(2):  # ← 縮排 1 層，外層 for 裡的內層 for
        total += 1  # ← 縮排 2 層，屬於內層 for
        print(f"    j={j}, total={total}")  # ← 縮排 2 層

    print("外圈結束")  # ← 回到縮排 1 層，又屬於外層 for

print(f"\n最後 total = {total}")  # ← 沒縮排，迴圈全部跑完才執行
