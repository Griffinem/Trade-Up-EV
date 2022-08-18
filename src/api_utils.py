# Globals
api_price_data_base = 'https://bitskins.com/api/v1/get_steam_price_data/?'

'''
Generates an API url.

Paramaters:
	base - base URL
	params - dict of params in the form {name: value}
'''
def generate_url(base=api_price_data_base, params=None):
	url = base
	for (i, key) in enumerate(params.keys()):
		
		# Append '&' to the start if you're not the first parameter
		if i != 0:
			url += '&'
		
		url += str(key) + '=' + str(params[key])
	
	return url