// Comprehensive North American Country, State/Province, and City Dataset for Commercial Buyer Discovery

export const COUNTRIES = [
  { id: 'BOTH', name: 'Both Countries (USA & Canada)', flag: '🌎' },
  { id: 'USA', name: 'United States (USA)', flag: '🇺🇸' },
  { id: 'Canada', name: 'Canada', flag: '🇨🇦' }
];

export const MAJOR_US_CITIES = [
  'Atlanta', 'Austin', 'Baltimore', 'Boston', 'Charlotte', 'Chicago', 'Cincinnati', 'Cleveland',
  'Columbus', 'Dallas', 'Denver', 'Detroit', 'Fort Worth', 'Honolulu', 'Houston', 'Indianapolis',
  'Jacksonville', 'Kansas City', 'Las Vegas', 'Los Angeles', 'Memphis', 'Miami', 'Milwaukee',
  'Minneapolis', 'Nashville', 'New Orleans', 'New York City', 'Oklahoma City', 'Orlando',
  'Philadelphia', 'Phoenix', 'Pittsburgh', 'Portland', 'Raleigh', 'Sacramento', 'Salt Lake City',
  'San Antonio', 'San Diego', 'San Francisco', 'San Jose', 'Seattle', 'St. Louis', 'Tampa', 'Washington D.C.'
];

export const MAJOR_CA_CITIES = [
  'Calgary', 'Edmonton', 'Halifax', 'Hamilton', 'Kelowna', 'Kitchener', 'London', 'Mississauga',
  'Montreal', 'Niagara Falls', 'Ottawa', 'Quebec City', 'Regina', 'Saskatoon', 'St. John\'s',
  'Surrey', 'Toronto', 'Vancouver', 'Victoria', 'Windsor', 'Winnipeg'
];

export const MAJOR_BOTH_CITIES = [
  'Atlanta', 'Austin', 'Boston', 'Calgary', 'Charlotte', 'Chicago', 'Dallas', 'Denver',
  'Edmonton', 'Houston', 'Las Vegas', 'Los Angeles', 'Miami', 'Minneapolis', 'Montreal',
  'Nashville', 'New York City', 'Ottawa', 'Philadelphia', 'Phoenix', 'Portland', 'San Antonio',
  'San Diego', 'San Francisco', 'Seattle', 'Toronto', 'Vancouver', 'Washington D.C.'
];

export const USA_STATES = [
  {
    code: 'ALL_US',
    name: 'All States/Provinces',
    cities: ['All Cities', ...MAJOR_US_CITIES]
  },
  {
    code: 'AL',
    name: 'Alabama',
    cities: ['All Cities', 'Birmingham', 'Huntsville', 'Mobile', 'Montgomery', 'Tuscaloosa', 'Auburn', 'Decatur', 'Dothan', 'Hoover', 'Tuskegee', 'Florence', 'Madison']
  },
  {
    code: 'AK',
    name: 'Alaska',
    cities: ['All Cities', 'Anchorage', 'Fairbanks', 'Juneau', 'Sitka', 'Ketchikan', 'Wasilla', 'Kenai', 'Kodiak']
  },
  {
    code: 'AZ',
    name: 'Arizona',
    cities: ['All Cities', 'Phoenix', 'Tucson', 'Mesa', 'Chandler', 'Scottsdale', 'Glendale', 'Tempe', 'Peoria', 'Surprise', 'Gilbert', 'Flagstaff', 'Yuma', 'Sedona']
  },
  {
    code: 'AR',
    name: 'Arkansas',
    cities: ['All Cities', 'Little Rock', 'Fayetteville', 'Fort Smith', 'Springdale', 'Jonesboro', 'Rogers', 'Conway', 'Bentonville', 'Pine Bluff', 'Hot Springs']
  },
  {
    code: 'CA',
    name: 'California',
    cities: ['All Cities', 'Los Angeles', 'San Francisco', 'San Diego', 'San Jose', 'Sacramento', 'Fresno', 'Long Beach', 'Oakland', 'Anaheim', 'Irvine', 'Santa Ana', 'Riverside', 'Stockton', 'Fremont', 'Beverly Hills', 'Pasadena', 'Santa Monica', 'Santa Barbara', 'Palo Alto', 'Bakersfield', 'Berkeley', 'Huntington Beach', 'Newport Beach']
  },
  {
    code: 'CO',
    name: 'Colorado',
    cities: ['All Cities', 'Denver', 'Colorado Springs', 'Aurora', 'Fort Collins', 'Lakewood', 'Thornton', 'Arvada', 'Westminster', 'Pueblo', 'Boulder', 'Greeley', 'Aspen', 'Vail']
  },
  {
    code: 'CT',
    name: 'Connecticut',
    cities: ['All Cities', 'Bridgeport', 'New Haven', 'Stamford', 'Hartford', 'Waterbury', 'Norwalk', 'Danbury', 'New Britain', 'Greenwich', 'Fairfield', 'Bristol', 'West Hartford']
  },
  {
    code: 'DE',
    name: 'Delaware',
    cities: ['All Cities', 'Wilmington', 'Dover', 'Newark', 'Middletown', 'Smyrna', 'Milford', 'Seaford', 'Rehoboth Beach']
  },
  {
    code: 'DC',
    name: 'District of Columbia (D.C.)',
    cities: ['All Cities', 'Washington D.C.', 'Georgetown', 'Capitol Hill', 'Dupont Circle', 'Downtown D.C.']
  },
  {
    code: 'FL',
    name: 'Florida',
    cities: ['All Cities', 'Miami', 'Orlando', 'Tampa', 'Jacksonville', 'St. Petersburg', 'Hialeah', 'Tallahassee', 'Fort Lauderdale', 'Port St. Lucie', 'Cape Coral', 'Pembroke Pines', 'Sarasota', 'Boca Raton', 'West Palm Beach', 'Naples', 'Clearwater', 'Gainesville', 'Key West', 'Coral Gables']
  },
  {
    code: 'GA',
    name: 'Georgia',
    cities: ['All Cities', 'Atlanta', 'Savannah', 'Augusta', 'Columbus', 'Macon', 'Athens', 'Sandy Springs', 'Roswell', 'Johns Creek', 'Alpharetta', 'Marietta', 'Decatur']
  },
  {
    code: 'HI',
    name: 'Hawaii',
    cities: ['All Cities', 'Honolulu', 'Hilo', 'Pearl City', 'Kailua', 'Waipahu', 'Kaneohe', 'Kahului', 'Kihei', 'Lahaina']
  },
  {
    code: 'ID',
    name: 'Idaho',
    cities: ['All Cities', 'Boise', 'Meridian', 'Nampa', 'Idaho Falls', 'Caldwell', 'Pocatello', 'Coeur d\'Alene', 'Twin Falls', 'Lewiston', 'Sun Valley']
  },
  {
    code: 'IL',
    name: 'Illinois',
    cities: ['All Cities', 'Chicago', 'Aurora', 'Naperville', 'Joliet', 'Rockford', 'Springfield', 'Elgin', 'Peoria', 'Champaign', 'Evanston', 'Schaumburg', 'Oak Park', 'Bloomington']
  },
  {
    code: 'IN',
    name: 'Indiana',
    cities: ['All Cities', 'Indianapolis', 'Fort Wayne', 'Evansville', 'South Bend', 'Carmel', 'Fishers', 'Bloomington', 'Hammond', 'Gary', 'Lafayette', 'Muncie', 'Terre Haute']
  },
  {
    code: 'IA',
    name: 'Iowa',
    cities: ['All Cities', 'Des Moines', 'Cedar Rapids', 'Davenport', 'Sioux City', 'Iowa City', 'Waterloo', 'Ames', 'West Des Moines', 'Dubuque', 'Council Bluffs']
  },
  {
    code: 'KS',
    name: 'Kansas',
    cities: ['All Cities', 'Wichita', 'Overland Park', 'Kansas City', 'Olathe', 'Topeka', 'Lawrence', 'Shawnee', 'Manhattan', 'Lenexa', 'Salina']
  },
  {
    code: 'KY',
    name: 'Kentucky',
    cities: ['All Cities', 'Louisville', 'Lexington', 'Bowling Green', 'Owensboro', 'Covington', 'Richmond', 'Georgetown', 'Florence', 'Hopkinsville', 'Frankfort']
  },
  {
    code: 'LA',
    name: 'Louisiana',
    cities: ['All Cities', 'New Orleans', 'Baton Rouge', 'Shreveport', 'Lafayette', 'Lake Charles', 'Kenner', 'Bossier City', 'Monroe', 'Alexandria', 'Houma']
  },
  {
    code: 'ME',
    name: 'Maine',
    cities: ['All Cities', 'Portland', 'Lewiston', 'Bangor', 'South Portland', 'Auburn', 'Biddeford', 'Augusta', 'Saco', 'Bar Harbor', 'Kennebunkport']
  },
  {
    code: 'MD',
    name: 'Maryland',
    cities: ['All Cities', 'Baltimore', 'Frederick', 'Rockville', 'Gaithersburg', 'Bowie', 'Hagerstown', 'Annapolis', 'Salisbury', 'Bethesda', 'Silver Spring', 'Columbia', 'College Park']
  },
  {
    code: 'MA',
    name: 'Massachusetts',
    cities: ['All Cities', 'Boston', 'Cambridge', 'Worcester', 'Springfield', 'Lowell', 'Brockton', 'Quincy', 'Lynn', 'New Bedford', 'Newton', 'Somerville', 'Brookline', 'Salem', 'Plymouth']
  },
  {
    code: 'MI',
    name: 'Michigan',
    cities: ['All Cities', 'Detroit', 'Grand Rapids', 'Warren', 'Sterling Heights', 'Ann Arbor', 'Lansing', 'Dearborn', 'Livonia', 'Troy', 'Kalamazoo', 'Flint', 'Traverse City']
  },
  {
    code: 'MN',
    name: 'Minnesota',
    cities: ['All Cities', 'Minneapolis', 'Saint Paul', 'Rochester', 'Bloomington', 'Duluth', 'Brooklyn Park', 'Plymouth', 'Woodbury', 'Lakeville', 'St. Cloud', 'Minnetonka']
  },
  {
    code: 'MS',
    name: 'Mississippi',
    cities: ['All Cities', 'Jackson', 'Gulfport', 'Southaven', 'Biloxi', 'Hattiesburg', 'Olive Branch', 'Tupelo', 'Meridian', 'Oxford', 'Starkville']
  },
  {
    code: 'MO',
    name: 'Missouri',
    cities: ['All Cities', 'Kansas City', 'Saint Louis', 'Springfield', 'Columbia', 'Independence', 'Lee\'s Summit', 'O\'Fallon', 'Saint Joseph', 'Saint Charles', 'Branson']
  },
  {
    code: 'MT',
    name: 'Montana',
    cities: ['All Cities', 'Billings', 'Missoula', 'Great Falls', 'Bozeman', 'Butte', 'Helena', 'Kalispell', 'Whitefish']
  },
  {
    code: 'NE',
    name: 'Nebraska',
    cities: ['All Cities', 'Omaha', 'Lincoln', 'Bellevue', 'Grand Island', 'Kearney', 'Fremont', 'Hastings', 'Norfolk', 'Columbus']
  },
  {
    code: 'NV',
    name: 'Nevada',
    cities: ['All Cities', 'Las Vegas', 'Henderson', 'Reno', 'North Las Vegas', 'Sparks', 'Carson City', 'Boulder City', 'Mesquite', 'Elko']
  },
  {
    code: 'NH',
    name: 'New Hampshire',
    cities: ['All Cities', 'Manchester', 'Nashua', 'Concord', 'Dover', 'Rochester', 'Portsmouth', 'Keene', 'Laconia', 'Hanover']
  },
  {
    code: 'NJ',
    name: 'New Jersey',
    cities: ['All Cities', 'Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Edison', 'Woodbridge', 'Lakewood', 'Toms River', 'Hamilton', 'Trenton', 'Princeton', 'Hoboken', 'Cherry Hill', 'Morristown']
  },
  {
    code: 'NM',
    name: 'New Mexico',
    cities: ['All Cities', 'Albuquerque', 'Las Cruces', 'Rio Rancho', 'Santa Fe', 'Roswell', 'Farmington', 'Clovis', 'Hobbs', 'Taos']
  },
  {
    code: 'NY',
    name: 'New York',
    cities: ['All Cities', 'New York City', 'Brooklyn', 'Manhattan', 'Queens', 'Bronx', 'Staten Island', 'Buffalo', 'Rochester', 'Yonkers', 'Syracuse', 'Albany', 'New Rochelle', 'Mount Vernon', 'Schenectady', 'Utica', 'White Plains', 'Ithaca', 'Saratoga Springs']
  },
  {
    code: 'NC',
    name: 'North Carolina',
    cities: ['All Cities', 'Charlotte', 'Raleigh', 'Greensboro', 'Durham', 'Winston-Salem', 'Fayetteville', 'Cary', 'Wilmington', 'High Point', 'Asheville', 'Concord', 'Gastonia', 'Chapel Hill']
  },
  {
    code: 'ND',
    name: 'North Dakota',
    cities: ['All Cities', 'Fargo', 'Bismarck', 'Grand Forks', 'Minot', 'West Fargo', 'Williston', 'Dickinson']
  },
  {
    code: 'OH',
    name: 'Ohio',
    cities: ['All Cities', 'Columbus', 'Cleveland', 'Cincinnati', 'Toledo', 'Akron', 'Dayton', 'Parma', 'Canton', 'Youngstown', 'Lorain', 'Hamilton', 'Springfield', 'Dublin']
  },
  {
    code: 'OK',
    name: 'Oklahoma',
    cities: ['All Cities', 'Oklahoma City', 'Tulsa', 'Norman', 'Broken Arrow', 'Edmond', 'Lawton', 'Moore', 'Midwest City', 'Enid', 'Stillwater']
  },
  {
    code: 'OR',
    name: 'Oregon',
    cities: ['All Cities', 'Portland', 'Eugene', 'Salem', 'Gresham', 'Hillsboro', 'Beaverton', 'Bend', 'Medford', 'Springfield', 'Corvallis', 'Lake Oswego', 'Ashland']
  },
  {
    code: 'PA',
    name: 'Pennsylvania',
    cities: ['All Cities', 'Philadelphia', 'Pittsburgh', 'Allentown', 'Reading', 'Erie', 'Upper Darby', 'Scranton', 'Bethlehem', 'Lancaster', 'Harrisburg', 'York', 'State College']
  },
  {
    code: 'RI',
    name: 'Rhode Island',
    cities: ['All Cities', 'Providence', 'Warwick', 'Cranston', 'Pawtucket', 'East Providence', 'Woonsocket', 'Newport', 'Cumberland', 'South Kingstown']
  },
  {
    code: 'SC',
    name: 'South Carolina',
    cities: ['All Cities', 'Charleston', 'Columbia', 'North Charleston', 'Mount Pleasant', 'Rock Hill', 'Greenville', 'Summerville', 'Goose Creek', 'Hilton Head Island', 'Myrtle Beach', 'Spartanburg']
  },
  {
    code: 'SD',
    name: 'South Dakota',
    cities: ['All Cities', 'Sioux Falls', 'Rapid City', 'Aberdeen', 'Brookings', 'Watertown', 'Mitchell', 'Pierre', 'Deadwood']
  },
  {
    code: 'TN',
    name: 'Tennessee',
    cities: ['All Cities', 'Nashville', 'Memphis', 'Knoxville', 'Chattanooga', 'Clarksville', 'Murfreesboro', 'Franklin', 'Johnson City', 'Jackson', 'Hendersonville', 'Gatlinburg']
  },
  {
    code: 'TX',
    name: 'Texas',
    cities: ['All Cities', 'Houston', 'San Antonio', 'Dallas', 'Austin', 'Fort Worth', 'El Paso', 'Arlington', 'Corpus Christi', 'Plano', 'Lubbock', 'Irving', 'Laredo', 'Garland', 'Frisco', 'McKinney', 'Amarillo', 'Grand Prairie', 'Brownsville', 'The Woodlands', 'Sugar Land', 'Round Rock']
  },
  {
    code: 'UT',
    name: 'Utah',
    cities: ['All Cities', 'Salt Lake City', 'West Valley City', 'Provo', 'West Jordan', 'Orem', 'Sandy', 'Ogden', 'St. George', 'Layton', 'Park City', 'Moab']
  },
  {
    code: 'VT',
    name: 'Vermont',
    cities: ['All Cities', 'Burlington', 'South Burlington', 'Rutland', 'Barre', 'Montpelier', 'Winooski', 'St. Albans', 'Stowe', 'Manchester']
  },
  {
    code: 'VA',
    name: 'Virginia',
    cities: ['All Cities', 'Virginia Beach', 'Richmond', 'Norfolk', 'Chesapeake', 'Newport News', 'Alexandria', 'Hampton', 'Roanoke', 'Portsmouth', 'Arlington', 'McLean', 'Fairfax', 'Charlottesville']
  },
  {
    code: 'WA',
    name: 'Washington',
    cities: ['All Cities', 'Seattle', 'Spokane', 'Tacoma', 'Vancouver', 'Bellevue', 'Kent', 'Everett', 'Renton', 'Spokane Valley', 'Kirkland', 'Bellingham', 'Redmond', 'Olympia', 'Yakima']
  },
  {
    code: 'WV',
    name: 'West Virginia',
    cities: ['All Cities', 'Charleston', 'Huntington', 'Morgantown', 'Parkersburg', 'Wheeling', 'Weirton', 'Fairmont', 'Martinsburg']
  },
  {
    code: 'WI',
    name: 'Wisconsin',
    cities: ['All Cities', 'Milwaukee', 'Madison', 'Green Bay', 'Kenosha', 'Racine', 'Appleton', 'Waukesha', 'Oshkosh', 'Eau Claire', 'Janesville', 'La Crosse']
  },
  {
    code: 'WY',
    name: 'Wyoming',
    cities: ['All Cities', 'Cheyenne', 'Casper', 'Laramie', 'Gillette', 'Rock Springs', 'Sheridan', 'Jackson', 'Cody']
  }
];

export const CANADA_PROVINCES = [
  {
    code: 'ALL_CA',
    name: 'All States/Provinces',
    cities: ['All Cities', ...MAJOR_CA_CITIES]
  },
  {
    code: 'AB',
    name: 'Alberta',
    cities: ['All Cities', 'Calgary', 'Edmonton', 'Red Deer', 'Lethbridge', 'St. Albert', 'Medicine Hat', 'Grande Prairie', 'Airdrie', 'Banff', 'Canmore', 'Fort McMurray']
  },
  {
    code: 'BC',
    name: 'British Columbia',
    cities: ['All Cities', 'Vancouver', 'Victoria', 'Surrey', 'Burnaby', 'Richmond', 'Kelowna', 'Abbotsford', 'Coquitlam', 'Kamloops', 'Nanaimo', 'Whistler', 'North Vancouver']
  },
  {
    code: 'MB',
    name: 'Manitoba',
    cities: ['All Cities', 'Winnipeg', 'Brandon', 'Steinbach', 'Thompson', 'Portage la Prairie', 'Winkler', 'Selkirk']
  },
  {
    code: 'NB',
    name: 'New Brunswick',
    cities: ['All Cities', 'Moncton', 'Saint John', 'Fredericton', 'Dieppe', 'Miramichi', 'Edmundston', 'Bathurst']
  },
  {
    code: 'NL',
    name: 'Newfoundland and Labrador',
    cities: ['All Cities', 'St. John\'s', 'Mount Pearl', 'Corner Brook', 'Conception Bay South', 'Grand Falls-Windsor', 'Gander']
  },
  {
    code: 'NS',
    name: 'Nova Scotia',
    cities: ['All Cities', 'Halifax', 'Sydney', 'Dartmouth', 'Truro', 'New Glasgow', 'Glace Bay', 'Kentville', 'Yarmouth']
  },
  {
    code: 'ON',
    name: 'Ontario',
    cities: ['All Cities', 'Toronto', 'Ottawa', 'Mississauga', 'Brampton', 'Hamilton', 'London', 'Markham', 'Vaughan', 'Kitchener', 'Windsor', 'Burlington', 'Greater Sudbury', 'Barrie', 'Guelph', 'Kingston', 'Oakville', 'Waterloo', 'Niagara Falls', 'Richmond Hill', 'Thunder Bay']
  },
  {
    code: 'PE',
    name: 'Prince Edward Island',
    cities: ['All Cities', 'Charlottetown', 'Summerside', 'Stratford', 'Cornwall', 'Montague']
  },
  {
    code: 'QC',
    name: 'Quebec',
    cities: ['All Cities', 'Montreal', 'Quebec City', 'Laval', 'Gatineau', 'Longueuil', 'Sherbrooke', 'Saguenay', 'Levis', 'Trois-Rivieres', 'Terrebonne', 'Saint-Jean-sur-Richelieu', 'Brossard', 'Drummondville']
  },
  {
    code: 'SK',
    name: 'Saskatchewan',
    cities: ['All Cities', 'Saskatoon', 'Regina', 'Prince Albert', 'Moose Jaw', 'Swift Current', 'Yorkton', 'North Battleford']
  },
  {
    code: 'NT',
    name: 'Northwest Territories',
    cities: ['All Cities', 'Yellowknife', 'Hay River', 'Inuvik', 'Fort Smith']
  },
  {
    code: 'NU',
    name: 'Nunavut',
    cities: ['All Cities', 'Iqaluit', 'Rankin Inlet', 'Arviat', 'Baker Lake']
  },
  {
    code: 'YT',
    name: 'Yukon',
    cities: ['All Cities', 'Whitehorse', 'Dawson City', 'Watson Lake', 'Haines Junction']
  }
];

export const STATES_BY_COUNTRY = {
  BOTH: [
    {
      code: 'ALL_BOTH',
      name: 'All States/Provinces',
      cities: ['All Cities', ...MAJOR_BOTH_CITIES]
    },
    ...USA_STATES.filter(s => s.code !== 'ALL_US').map(s => ({ ...s, name: `${s.name} (USA)` })),
    ...CANADA_PROVINCES.filter(p => p.code !== 'ALL_CA').map(p => ({ ...p, name: `${p.name} (Canada)` }))
  ],
  USA: USA_STATES,
  Canada: CANADA_PROVINCES
};

// Formats a clean location string for discovery query
export function buildLocationQuery(country, stateName, cityName, customCity = '') {
  const effectiveCity = customCity.trim() || (cityName && !cityName.startsWith('All') ? cityName : '');
  const parts = [];
  
  if (effectiveCity) {
    parts.push(effectiveCity);
  }

  const cleanState = (stateName || '')
    .replace(' (USA)', '')
    .replace(' (Canada)', '')
    .trim();

  if (cleanState && !cleanState.startsWith('All')) {
    parts.push(cleanState);
  }

  if (country === 'BOTH') {
    if (!cleanState || cleanState.startsWith('All')) {
      parts.push('United States, Canada');
    } else if (stateName && stateName.includes('(Canada)')) {
      parts.push('Canada');
    } else {
      parts.push('United States');
    }
  } else if (country === 'USA') {
    parts.push('United States');
  } else if (country === 'Canada') {
    parts.push('Canada');
  }

  return parts.join(', ');
}
