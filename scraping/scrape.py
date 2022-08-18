import requests
import json

from bs4 import BeautifulSoup

def make_case_or_collection_data(link):
	page = requests.get(link)
	soup = BeautifulSoup(page.text, features='lxml')
	
	main_content = soup.find_all('div', 'main-content')[0]
	main_divs = main_content.find_all('div', 'row', recursive=False)
	main_div = main_divs[5]
	
	collection_name = main_divs[2].div.find_all('div', 'collapsed-top-margin', recursive=False)[0].h1.text
	
	weapon_links = []
	for box in main_div.find_all('div', 'col-lg-4', recursive=False):
		#print(box)
		if 'adv-result-box-skins' not in box['class']:
			for a in box.div.find_all('a', recursive=False):
				if not a.has_attr('class'):
					weapon_links.append(a['href'])
	
	return (collection_name, weapon_links)

def make_weapon_data(links):
	data = {'consumer': [], 'industrial': [], 'milspec': [], 'restricted': [], 'classified': [], 'covert': []}
	for link in links:
		item = {}
		page = requests.get(link)
		soup = BeautifulSoup(page.text, features='lxml')
		
		main_content = soup.find_all('div', 'main-content')[0]
		info_div = main_content.find_all('div', 'row text-center')[0].find_all('div', 'col-md-10')[0].div
		
		img_div = info_div.find_all('div', 'col-md-7')[0]
		floatprice_div = info_div.find_all('div', 'col-md-5')[0]
		
		upper_img_div = img_div.find_all('div', 'result-box')[0]
		name_header = upper_img_div.h2
		rarity_div = upper_img_div.find_all('a', 'nounderline')[0].div
		
		wear_div = floatprice_div.find_all('div', 'wear-well')[0].div.div.div
		
		name = name_header.contents[0].text + ' | ' + name_header.contents[2].text
		rarity = rarity_div['class'][1][rarity_div['class'][1].index('-')+1:]
		#case_or_coll = img_div.find_all('div', 'skin-details-collection-container')[0].div.a.p.text
		wear_min = (float)(wear_div.find_all('div', 'marker-wrapper')[0].div.div.text)
		wear_max = (float)(wear_div.find_all('div', 'marker-wrapper')[1].div.div.text)

		item['name'] = name
		item['wear_min'] = wear_min
		item['wear_max'] = wear_max
		'''
		print(name)
		print(rarity)
		#print(case_or_coll)
		print(wear_min)
		print(wear_max)
		'''
		
		data[rarity].append(item)
	
	return data
	

if __name__ == '__main__':

	data = {}

	page = requests.get('https://www.csgostash.com')
	soup = BeautifulSoup(page.text, features='lxml')
	
	dropdown_lis = soup.find_all('li', 'dropdown')
	
	cases_ind, collections_ind = 0, 0
	
	for (i, li) in enumerate(dropdown_lis):
		if li.a.text == 'Cases':
			cases_ind = i
		elif li.a.text == 'Collections':
			collections_ind = i
	
	dropdown_cases = dropdown_lis[cases_ind]
	dropdown_collections = dropdown_lis[collections_ind]
	
	case_links = []
	collection_links = []

	# Get case URLs
	sections = 2
	for li in dropdown_cases.ul.find_all('li'):
		if li.has_attr('class'):
			if li['class'][0] == 'dropdown-header':
				continue
			elif li['class'][0] == 'divider':
				sections -= 1
				continue
		else:
			if sections > 0:
				case_links.append(li.a['href'])
				
	# Get collection URLs
	for li in dropdown_collections.ul.find_all('li'):
		if not li.has_attr('class'):
			collection_links.append(li.a['href'])
			
	#print(case_links)
	#print(collection_links)
	
	# Create data sets
	for (i, case_link) in enumerate(case_links):
		link_list_tuple = make_case_or_collection_data(case_link)
		data[link_list_tuple[0]] = make_weapon_data(link_list_tuple[1])
		
	for (i, coll_link) in enumerate(collection_links):
		link_list_tuple = make_case_or_collection_data(coll_link)
		data[link_list_tuple[0]] = make_weapon_data(link_list_tuple[1])
		
	
	weapon_data_file = open('_data_file.json', 'w')
	json.dump(data, weapon_data_file)
	
	
	print('Done!')
	
	
	
	