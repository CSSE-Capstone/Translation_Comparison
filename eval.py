manualtranslation = pd.read_csv('manualtranslationtest.csv')

# check cardinality, population,
checks = []
for index, row in manualtranslation.iterrows():
   if row['Subject'] == row['Indicator'] or row['Subject'] == row['Indicator']+'Population':
     checks.append([row['Indicator'],[[row['Subject'],row['Value']],row['Property']],'autocheck'])
   else:
     checks.append([row['Indicator'],[[row['Subject'],row['Value']],row['Property']],'manualcheck'])

for c in checks:
  if c[2] == 'autocheck':
    if c[1] in prop_rel:
      c.append(1)
    else:
      c.append(0)

checks = pd.DataFrame(checks)
checks.head()