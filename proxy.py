from flask import Flask, Response, request, url_for
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import os
import io
import urllib.request
import random
app = Flask(__name__)

@app.route('/')
def printUsage():
	return "TODO"

@app.route('/<path:url>')
def proxy(url):
	protocol = "http://"
	full_url = protocol+url
	if len(request.query_string) != 0:
		full_url += "?"+request.query_string.decode('utf-8')
	print('DEBUG:', full_url)
	response = urllib.request.urlopen(full_url)
	print(response.info()['Content-Type'])
	mimetype = response.info()['Content-Type'].split(';',1)[0]
	data = None
	if mimetype.startswith("image/"):
		extension = mimetype.split("/")[-1]
		dimension = Image.open(io.BytesIO(response.read())).size
		print("Trying to get ", extension, " with ", dimension)
		image_to_load = get_image(extension, dimension)
		f = open(image_to_load,"rb")
		data = f.read()
		f.close()
	elif mimetype == "text/html":
		soup = BeautifulSoup(response.read())
		to_rewrite = soup.find_all(needs_rewrite)
		for elem in to_rewrite:
			for attr in rewrite_attributes:
				if elem.has_attr(attr):
					elem[attr] = rewrite_url(full_url, elem[attr])
		data = str(soup)
	else:
		data = response.read()
	return Response(data, status=response.getcode(),
			headers=response.getheaders())

rewrite_attributes = ['href','src']
def needs_rewrite(tag):
	global rewrite_attributes
	for a in rewrite_attributes:
		if tag.has_attr(a):
			return True
	return False

def rewrite_url(full_url, relative_url):
	global app
	total_url = urljoin(full_url, relative_url)
	print('DEBUG:',total_url)
	try:
		argument = total_url.split('://',1)[1]
	except IndexError:
		return relative_url
	#print(www.config['HOST'])
	end_result = url_for('proxy', url=argument)
	#end_result = "http://"+app.config['SERVER_NAME']+"/"+argument
	print(full_url, relative_url, total_url, end_result)
	return end_result

def get_image(extension, dimension):
	possible = cat_images[extension]
	print(possible)
	random.shuffle(possible)
	best = possible[0]
	for image in possible[1:]:
		if total_error(dimension, best[1]) > total_error(dimension, image[1]):
			best = image
		elif total_error(dimension, best[1]) == total_error(dimension, image[1]) and ratio_error(dimension, best[1]) > total_error(dimension, image[1]):
			best = image
	return best[0]
#get_image returns file name with
# minimal total area and minimal stretched area difference

cat_images ={}
def populate_images(dirs):
	global cat_images
	for files in os.listdir(dirs):
		full_path = os.path.join(dirs, files)
		extension = files.split('/')[-1].split('.',1)[-1]
		if extension not in cat_images.keys():
			cat_images[extension] = []
		dimension = Image.open(full_path).size
		cat_images[extension].append((full_path, dimension))
	print(cat_images)

def total_error(dimA, dimB):
	return (dimA[0]*dimA[1] - dimB[0]*dimB[1])**2

def ratio_error(dimA, dimB):
	nDimA_1 = float(dimA[0])/dimB[0]*dimB[1]
	nDimA_0 = float(dimA[1])/dimA[1]*dimB[0]
	return min(total_error((dimA[0], nDimA_1), dimB),
			total_error((nDimA_0, dimA[1]), dimB))

if __name__ == '__main__':
	populate_images("images/")
	app.run(debug=True)
