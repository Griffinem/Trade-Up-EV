#from api_utils import *

import json
import requests
import time

item_price_data_url 	= 'http://csgobackpack.net/api/GetItemsList/v2/'
weapon_data_file_path	= '..\scraping\weapon_data_file.json'
ev_output_file_path		= 'ev_data_file.json'

float_cutoffs 	= {'Factory New': [0.0, 0.07], 'Minimal Wear': [0.07, 0.15], 'Field-Tested': [0.15, 0.38], 'Well-Worn': [0.38, 0.45], 'Battle-Scarred': [0.45, 1.0]}
wear_int_dict 	= {0: 'Factory New', 1: 'Minimal Wear', 2: 'Field-Tested', 3: 'Well-Worn', 4: 'Battle-Scarred'}
grade_int_dict 	= {0: 'consumer', 1: 'industrial', 2: 'milspec', 3: 'restricted', 4: 'classified', 5: 'covert'}

metadata 	= {}
ev_dict 	= {}

def get_item_best_wear(wear_min):
	if wear_min < float_cutoffs['Factory New'][1]:
		return 0
	elif wear_min < float_cutoffs['Minimal Wear'][1]:
		return 1
	elif wear_min < float_cutoffs['Field-Tested'][1]:
		return 2
	elif wear_min < float_cutoffs['Well-Worn'][1]:
		return 3
	else:
		return 4
		
def get_item_worst_wear(wear_max):
	if wear_max >= float_cutoffs['Battle-Scarred'][0]:
		return 4
	elif wear_max >= float_cutoffs['Well-Worn'][0]:
		return 3
	elif wear_max >= float_cutoffs['Field-Tested'][0]:
		return 2
	elif wear_max >= float_cutoffs['Minimal Wear'][0]:
		return 1
	else:
		return 0
		
def get_tradeup_ev(coll, grade):
	for (i, weapon_i) in enumerate(coll[ grade_int_dict[grade] ]):
		# Get best wear and worst wear as int
		item_best_wear, item_worst_wear = get_item_best_wear(weapon_i['wear_min']), get_item_worst_wear(weapon_i['wear_max'])
	
		''' The tertiary loop will iterate over each weapon wear '''
		for wear_val in range(item_best_wear, item_worst_wear+1):
			break_val = False
			# Get the tradeup cost
			weapon_key_str = weapon_i['name'] + ' (' + wear_int_dict[wear_val] + ')'
			try:
				tradeup_cost = price_data[weapon_key_str]['price'][ metadata['time'] ][ metadata['metric'] ] * 10
			except KeyError:
				#print('Error getting {0}.  Breaking...'.format(weapon_key_str))
				break_val = True
				break
				
			#print('Trading up {}'.format(weapon_key_str))
			
			# Get tradeup float avg
			tradeup_float_avg = 0.0
			if metadata['float'] == 'median':
				# Special cases
				if wear_val == item_best_wear:
					tradeup_float_avg = (weapon_i['wear_min'] + float_cutoffs[ wear_int_dict[wear_val] ][1]) / 2.0
				elif wear_val == item_worst_wear:
					tradeup_float_avg = (float_cutoffs[ wear_int_dict[wear_val] ][0] + weapon_i['wear_max']) / 2.0
				#Default
				else:
					tradeup_float_avg = (float_cutoffs[ wear_int_dict[wear_val] ][0] + float_cutoffs[ wear_int_dict[wear_val] ][1]) / 2.0
			
			elif metadata['float'] == 'min':
				# Special cases
				if wear_val == item_best_wear:
					tradeup_float_avg = weapon_i['wear_min']
				# Default
				else:
					tradeup_float_avg = float_cutoffs[ wear_int_dict[wear_val] ][0]
					
			elif metadata['float'] == 'max':
				# Special cases
				if wear_val == item_worst_wear:
					tradeup_float_avg = weapon_i['wear_max']
				# Default
				else:
					tradeup_float_avg = float_cutoffs[ wear_int_dict[wear_val] ][1]
					
			
			''' The quat...iary loop will iterate over each weapon in the next-highest weapon group to get the EV'''
			ev = 0
			tradeup_gross_list = []
			all_profit = True
			for (j, weapon_tu_j) in enumerate(coll[ grade_int_dict[grade+1] ]):
				# Calculation:
				# Resulting Float = (Avg(Tradeup Float) * [Result_Max - Result_Min]) + Result_Min
				j_float = (tradeup_float_avg * (weapon_tu_j['wear_max'] - weapon_tu_j['wear_min'])) + weapon_tu_j['wear_min']
				j_wear = 0
				if j_float < 0.07:
					j_wear = 0
				elif j_float < 0.15:
					j_wear = 1
				elif j_float < 0.38:
					j_wear = 2
				elif j_float < 0.45:
					j_wear = 3
				else:
					j_wear = 4
				
				j_weapon_key_str = weapon_tu_j['name'] + ' (' + wear_int_dict[j_wear] + ')'
				try:
					tradeup_net = price_data[j_weapon_key_str]['price'][ metadata['time'] ][ metadata['metric'] ]
				except KeyError:
					#print('Error getting {0}.  Breaking...'.format(j_weapon_key_str))
					break_val = True
					break
				# Rough gross value - steam fees
# TODO: Modify this to work with bitskins/other site prices
				tradeup_gross = tradeup_net * 0.87
				
				# For checking variance
				tradeup_gross_list.append(tradeup_gross)
				
				# For checking all profit
				profit = tradeup_gross - tradeup_cost
				if profit < 0:
					all_profit = False
				
				#print('1/{0} chance for {1}'.format(len(coll[ grade_int_dict[grade+1] ]), j_weapon_key_str))
				ev += ( (profit) / len(coll[ grade_int_dict[grade+1] ]) )
				
			if break_val != True:
				#print('Trade up 10x {0} at {1} float values results in Expected Value of ${2:.4f}'.format(weapon_key_str, metadata['float'], ev))
				ev_dict[weapon_key_str] = [ev, tradeup_cost, tradeup_gross_list, all_profit]
				

if __name__ == '__main__':
	ev_output_file_path = str(input('Enter output file path ("ev_output_file_.json"): '))
	
	''' Gather metadata for query params '''
	md_time = str(input('Enter price search time [24_hours, 7_days, 30_days, all_time]: '))
	while md_time not in ['24_hours', '7_days', '30_days', 'all_time']:
		md_time = str(input('Please enter one of the following price search times [24_hours, 7_days, 30_days, all_time]: '))
	metadata['time'] = md_time
	
	md_metric = str(input('Enter price metric [median, average, lowest_price, highest_price]: '))
	while md_metric not in ['median', 'average', 'lowest_price', 'highest_price']:
		md_metric = str(input('Please enter one of the following price metrics [median, average, lowest_price, highest_price]: '))
	metadata['metric'] = md_metric
	
	#md_sold_min = int(input('Enter minimum sold (holds for all items individually in the calculation): '))
	#while type(md_sold_min) != 'int':
	#	md_sold_min = input('Please enter an integer value: ')
	#metadata['sold_min'] = int(md_sold_min)
	
	md_float = str(input('Enter float [min, median, max]: '))
	while md_float not in ['min', 'median', 'max']:
		md_float = str(input('Float must be in [min, median, max]: '))
	metadata['float'] = md_float
	
	
	''' Generate price data from csgobackpack API '''
	start_a = time.time()
	
	response = requests.get(item_price_data_url).json()
	
	timestamp 	= response['timestamp']
	price_data 	= response['items_list']
	
	# Get items data from scraper (use utf8 for the chinese m4 I think)
	with open(weapon_data_file_path, 'r', encoding='utf8') as weapon_data_file:
		weapon_data = json.load(weapon_data_file)
	
	elapsed_a = time.time() - start_a
	
	print('Load finished in {0} seconds'.format(elapsed_a))
	
	
	''' The main loop will iterate over individual case/collection '''
	start_b = time.time()
	
	for key in weapon_data.keys():
		coll = weapon_data[key]
		
		''' The secondary loop will iterate over rarity '''
		## Consumer Grade
		if len(coll['industrial']) > 0:
			get_tradeup_ev(coll, 0)
		## Industrial Grade
		if len(coll['milspec']) > 0:
			get_tradeup_ev(coll, 1)
		## Mil-Spec Grade
		if len(coll['restricted']) > 0:
			get_tradeup_ev(coll, 2)
		## Restricted Grade
		if len(coll['classified']) > 0:
			get_tradeup_ev(coll, 3)
		## Classified Grade
		if len(coll['covert']) > 0:
			get_tradeup_ev(coll, 4)
	
	elapsed_b = time.time() - start_b
	
	ev_dict_sorted = {k: v for k, v in sorted(ev_dict.items(), key=lambda item: item[1], reverse=True)}
	
	with open(ev_output_file_path, 'w', encoding='utf8') as ev_output_file:
		json.dump(ev_dict_sorted, ev_output_file)
	
	print('EV check finished in {0} seconds'.format(elapsed_b))