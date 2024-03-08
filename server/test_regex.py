import re

email = "Subject: Improve Your Financial Health with Surge Credit Card!\n\nHello Erik,\n\nI hope this email finds you well! My name is Michael, and I'm reaching out from Continental Finance Company. I understand the importance of managing your finances, especially as a college student in the bustling tech scene of Seattle.\n\nI wanted to introduce you to Surge, our credit card designed to help you build better spending habits and work towards a healthier financial future. With low fees and a modest credit limit, Surge is perfect for basic purchases like food and clothing - making it perfect for your needs.\n\nAs a young adult, it's crucial to start establishing good credit early on. Surge reports your credit activity to three bureaus, helping you improve your credit over time. Additionally, our tracking features can assist you in managing your spending effectively.\n\nI believe Surge can help you on your journey towards financial success. Feel free to reach out with any questions or to learn more.\n\nBest regards,\n\nMichael\nContinental Finance Company"

print(re.findall(r'Subject[^\n]*\n\n', email)[0][:-2])

print(re.findall(r'\n\n[^"]*', email)[0][2:])