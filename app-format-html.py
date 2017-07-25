from bs4 import BeautifulSoup as BS
import urllib2
import os, json, re

site_url = 'http://cmol.creditmantri.in/' #'https://www.creditmantri.com/'
filename = './links.json'
htmlpath = './html/'
format_html = True

bs4_prettify = BS.prettify
regex_pretty = re.compile(r'^(\s*)', re.MULTILINE)
def prettify(self, encoding = None, formatter = 'minimal', indent = 4):
	return regex_pretty.sub(r'\1' * indent, bs4_prettify(self)) #, encoding, formatter))

BS.prettify = prettify	 

def makdir(path):
	try:	
		os.makedirs(path)
	except:
		pass	

def filetostr(filename):
	with open(filename) as f:
		return f.readlines()

def jsontostr(filename):
	with open(filename) as f:
		contents = f.read()
	try:
		return json.loads(contents.replace('\\\\"', '\''))
	except:
		print "Error: Invalid Json file!"	


def download(url):
	html = ''
	download_size = 0
	buffer_size = 8192
	s = url.strip().split('/')
	filename = s[-2] if s[-1] == '' else s[-1]

	try:
		u = urllib2.urlopen(url)
		meta = u.info()

		try:
			filesize = int(meta.getheaders('Content-Length')[0])
		except:
			filesize = 1
		print "Downloading ... \"%s\" Size: %s kb" % (url, filesize/1024) 
		
		while True:
			buffer = u.read(buffer_size)
			if not buffer:
				break;

			download_size += buffer_size
			html += buffer
			status = "Downloaded: %s kb [%3.2f %%]" % (download_size/1024, ((download_size/100.)* filesize))
			status = status + chr(8)*(len(status)+1)
			print status,

		print status
		return filename, html 
	except urllib2.HTTPError as e:
		return -1, str(e) 

def parse(filename, html):

	# <div class="pd-tp-20 pd-bt-20 equifax-content" (about-equifax-india)
	#	- <div class="col-sm-9"

	# <div class="col-sm-8 col-lg-9					(credit-card-customer-care | fixed-deposit-rate)
	# <div class="col-sm-9 pd-tp-20"				(-credit-card-customer-care-number | -fixed-deposit-rate)
	# <div class=""

	# <section class="container-fluid pd20" 		(*-loan)
	#				="container-fluid pd20" 	

	# (jaipur-credit-card)

	soup = BS(html, "lxml")
	pat = 'section.container-fluid.pd20'
	if filename == 'about-equifax-india':
		pat = 'div.pd-tp-20.pd-bt-2.equifax-content div.col-sm-9'
	elif filename == 'credit-card-customer-care' or filename == 'fixed-deposit-rate':
		pat = 'div.col-sm-8.col-lg-9'
	elif '-credit-card-customer-care-number' in filename or '-fixed-deposit-rate' in filename:
		pat = 'div.col-sm-9.pd-tp-20'
	elif '-credit-card' in filename:
		pat = 'div.lendersnew-layout div.container'	

	tags = soup.select(pat)
	html = ''.join(str(tag) for tag in tags)

	soup = BS(html, "lxml")
	for tag in soup.findAll(True):
		for attr in ['id', 'class', 'style']:
			del tag[attr]
	if format_html:		
		return soup.prettify().encode("utf-8")	
	return str(soup.find('body').findChildren()[0]).replace('\n', '')	

def write_file(filename, html):
	f = open(htmlpath + filename + '.html', 'wb')

	f.write(html)
	f.close()	

if __name__ == '__main__':

	makdir(htmlpath)
	fh = open('./log.txt', 'w')

	ext = filename.split('.')[-1]
	if (ext == 'json'):
		urls = jsontostr(filename)['data']
	else:	
		urls = filetostr(filename)

	i = 0	
	for url in urls:
		i += 1
		if i > 1:
			break
		elif (ext == 'json'):
			url = site_url + url['url']
		elif url.strip() == '' or '#------' in url:
			continue

		filename, html = download(url)
		if filename == -1:
			# Download failed
			url = '[Error\t]: %s (%r)' % (url, html)
		else:	 
			#print "Parsing ... \"%s\"" % filename
			html = parse(filename, html)
			write_file(filename, html)
			url = '[Ok  \t]: ' + url

		fh.write(url + os.linesep)
		print url
		
	fh.close()	

