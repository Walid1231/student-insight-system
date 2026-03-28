with open('templates/student_analytics.html', 'r', encoding='utf-8') as f:
    c = f.read()
c2 = c.replace('?v=3', '?v=4')
with open('templates/student_analytics.html', 'w', encoding='utf-8') as f:
    f.write(c2)
print('v=4 count:', c2.count('?v=4'))
