def send_mail(context, stocklist, advlist, title, info, sumup=""):
    if not g.open_gmail:
        return False
    host = g.gmail_host
    port = g.gmail_port
    sender = g.gmail_sender
    authcode = g.gmail_authcode
    receivers = g.gmail_receivers
    stockstr = ''
    for i, stock in enumerate(stocklist):
        stockcode = stock.split(".")[0]
        price_now = attribute_history(stock, 1, '1m', 'close')['close'][0]
        stockstr += f'{i+1}. {get_security_info(stock).display_name}: {stock}  最新价：{price_now}'\
                    f'{advlist[i]}  查看📖'
    mail_msg = f'{info}{str(context.current_dt)}股票列表: {stockstr}{sumup}'
    try:
        smtp = smtplib.SMTP(host, port)  
        smtp.login(sender, authcode)  
        for tomail in receivers:
            message = MIMEText(mail_msg, 'html', 'utf-8')
            fromnick = sender.split('@')[0]
            fromnickname64str = str(base64.b64encode(fromnick.encode()), 'utf-8')
            message['From'] = Header(f'"=?utf-8?B?{fromnickname64str}?=" <{sender}>')
            message['Subject'] = Header(title, 'utf-8')
            nickname64str = str(base64.b64encode(tomail.split('@')[0].encode()), 'utf-8')
            message['To'] = Header(f'"=?utf-8?B?{nickname64str}?=" <{tomail}>')
            smtp.sendmail(sender, [tomail], message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")
    finally:
        smtp.quit()

复制
