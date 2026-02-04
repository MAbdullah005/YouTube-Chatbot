import smtplib

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("abdullahaliofc@gmail.com", "cbwnhnzhzbgneovc")
print("LOGIN SUCCESS")
server.quit()
