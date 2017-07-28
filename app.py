#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as BS
import urllib2
import os, json, re
from htmlmin.minify import html_minify

import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from config import *
from db import *

linesep = os.linesep
bs4_prettify = BS.prettify
regex_pretty = re.compile(r'^(\s*)', re.MULTILINE)
def prettify(self, encoding = "ascii", formatter = 'html', indent = 4):
	return regex_pretty.sub(r'\1' * indent, bs4_prettify(self, encoding, formatter))

BS.prettify = prettify	 

def compress(html):
	return html_minify(html).replace('<html><head></head><body>', '').replace('</body></html>', '') #, remove_empty_space = True)

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

def extract(tags, index = [-1]):
	html = ''.join(str(tag) for tag in tags)
	soup = BS(html, "lxml").find('body')
	
	try:
		children = soup.findChildren(recursive=False)##[0]
	except Exception as e:
		print "[Soup Error]: %s" % str(e)
		return ''
	
	i = -1
	html = ''
	for child in children:
		i += 1
		if index[0] != -1 and i not in index:
			continue 

		for tag in child.findParent().findAll(True):
			for attr in ['id', 'class', 'style']:
				del tag[attr]

		html += child.prettify().encode('ascii', 'replace').decode('ascii')

	return html	


def parse(filename, html):

	# <div class="pd-tp-20 pd-bt-20 equifax-content" (about-equifax-india)
	#	- <div class="col-sm-9"

	# <div class="col-sm-8 col-lg-9					(credit-card-customer-care | fixed-deposit-rate)
	# <div class="col-sm-9 pd-tp-20"				(-credit-card-customer-care-number | -fixed-deposit-rate)
	
	# <section class="container-fluid pd20" 		(*-loan)
	# container-fluid pd20, 3 						(shopping-credit-cards) 

	index = [-1]
	soup = BS(html, "lxml")

	content = ''
	tags = soup.select('div#no-products')
	header = extract(tags)

	pat = 'section.container-fluid.pd20'
	if filename == 'about-equifax-india':
		pat = 'div.pd-tp-20.pd-bt-2.equifax-content div.col-sm-9'
	elif filename == 'credit-card-customer-care' or filename == 'fixed-deposit-rate':
		pat = 'div.col-sm-8.col-lg-9'
	elif '-credit-card-customer-care-number' in filename or '-fixed-deposit-rate' in filename:
		pat = 'div.col-sm-9.pd-tp-20'
	elif '-credit-card' in filename:
		if 'lifestyle' in filename or 'fuel' in filename or 'shopping' in filename or 'cashback' in filename or 'travel' in filename or 'entertainment' in filename or filename.partition(' ')[0] == 'rewards':
			index = [1]
			pat = 'div.lendersnew-layout > section.container-fluid.pd20'
		else :
			pat = 'div.lendersnew-layout > div.container'
	elif '-personal-loan':
		pat = 'div.lendersnew-layout'
		tags = soup.select(pat + ' > section.container-fluid')
		content += extract(tags, [2])
		pat += ' > div.container'	

	tags = soup.select(pat)
	content += extract(tags, index)	# index => Array of index values start from 0 (Ex. index = [0, 1, 3] or "[-1]" for all)
	return header, content

def write_file(filename, html):
	f = open(htmlpath + filename + '.html', 'wb')

	f.write(html)
	f.close()	

if __name__ == '__main__':

	db = DB()
	db.connect()
	
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
		if i > 1000000:
			break
		elif (ext == 'json'):
			name = url['label']
			url = site_url + url['url']
		elif url.strip() == '' or '#------' in url:
			continue

		filename, html = download(url)
		if filename == -1:
			# Download failed
			url = '[Error\t]: %s (%r)' % (url, html)
		else:	 
			header, content = parse(filename, html)
			write_file(filename, header + '<!-- CONTENT BEGINS -->' + content)
			args = {
				'name'  : name,
				'slug' 	: filename,
				'url'	: url,
				'header': compress(header), #.replace(linesep, ''),
				'content': compress(content) #content.replace(linesep, '') 
			}
			db.insert(args)

			if not content:
				url_prefix = '[Empty\t]' 
			else:
				url_prefix = '[Ok  \t]'
			url = url_prefix + ': ' + url

		fh.write(url + linesep)
		print url
		
	fh.close()	
	db.close()
	