// Editorial crop descriptions and DEMO sorting. No region-specific suitability is claimed.
// Region / country / category labels live in i18n.js (keys r.*, c.*, cat.*, wat.*, sea.*).
import {t,pick} from './i18n.js';
export const regions = {
 'TJK':[{id:'TJK-KHT'},{id:'TJK-SUG'},{id:'TJK-RRP'},{id:'TJK-GBA'}],
 'USA':[{id:'USA-NE-SC'}]
};
export const countryOf = regionId => regionId.startsWith('USA')?'USA':'TJK';
export const regionName = id => t('r.'+id);
const P={wheat:'https://images.unsplash.com/photo-1501436513145-30f24e19fcc4?w=1000&q=80',field:'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1000&q=80',veg:'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1000&q=80',green:'https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=1000&q=80'};
const C=(id,latin,cat,water,season,photo,name,desc)=>({id,latin,cat,water,season,photo,names:name,descs:desc});
export const cropList=[
 C('wheat','Triticum aestivum','cereals','medium','autumn_spring',P.wheat,{en:'Wheat',ru:'Пшеница',tg:'Гандум'},{en:'A cereal grown across many climate zones. Variety, sowing dates and irrigation depend on local conditions.',ru:'Зерновая культура, выращиваемая в разных климатических зонах. Сорт, сроки посева и полив зависят от местных условий.',tg:'Зироати ғалладонагӣ, ки дар минтақаҳои гуногуни иқлимӣ парвариш мешавад. Навъ, мӯҳлати кишт ва обёрӣ ба шароити маҳаллӣ вобаста аст.'}),
 C('cotton','Gossypium','technical','medium_high','warm',P.field,{en:'Cotton',ru:'Хлопчатник',tg:'Ғӯза'},{en:'A heat-loving industrial crop. It needs an assessment of the length of the warm period, soil and the availability of irrigation water.',ru:'Теплолюбивая техническая культура. Требует оценки длительности тёплого периода, почвы и доступности поливной воды.',tg:'Зироати техникии гармдӯст. Арзёбии давомнокии давраи гарм, хок ва дастрасии оби обёриро талаб мекунад.'}),
 C('corn','Zea mays','cereals','medium_high','warm',P.field,{en:'Corn',ru:'Кукуруза',tg:'Ҷуворимакка'},{en:'A crop with a high heat demand and a high need for water in critical growth stages. It needs hybrid selection and a local nutrition regime.',ru:'Культура с высокой потребностью в тепле и воде в критические фазы развития. Нужен подбор гибрида и местного режима питания.',tg:'Зироат бо талаботи баланд ба гармӣ ва об дар марҳилаҳои муҳими рушд. Интихоби гибрид ва низоми ғизодиҳии маҳаллиро талаб мекунад.'}),
 C('barley','Hordeum vulgare','cereals','medium','autumn_spring',P.wheat,{en:'Barley',ru:'Ячмень',tg:'Ҷав'},{en:'A cereal for which variety, season length and soil properties are critical.',ru:'Зерновая культура, для которой критичны сорт, продолжительность сезона и свойства почвы.',tg:'Зироати ғалладонагӣ, ки барои он навъ, давомнокии мавсим ва хосиятҳои хок муҳиманд.'}),
 C('tomato','Solanum lycopersicum','vegetables','regular','warm',P.veg,{en:'Tomato',ru:'Томат',tg:'Помидор'},{en:'A vegetable sensitive to frost, moisture imbalance and disease. It can be grown in the open or under cover.',ru:'Овощная культура, чувствительная к заморозкам, дисбалансу влаги и болезням. Может выращиваться в открытом или защищённом грунте.',tg:'Сабзавоте, ки ба сармо, номутавозунии намӣ ва бемориҳо ҳассос аст. Онро дар замини кушод ё пӯшида парвариш кардан мумкин аст.'}),
 C('potato','Solanum tuberosum','vegetables','regular','temperate',P.veg,{en:'Potato',ru:'Картофель',tg:'Картошка'},{en:'A tuber crop. Soil temperature, water supply and disease protection matter when assessing a site.',ru:'Клубнеплодная культура. Для оценки участка важны температура почвы, обеспеченность водой и защита от болезней.',tg:'Зироати лаппагӣ. Барои арзёбии майдон ҳарорати хок, таъмини об ва ҳимоя аз бемориҳо муҳиманд.'}),
 C('rice','Oryza sativa','cereals','high','warm',P.field,{en:'Rice',ru:'Рис',tg:'Шолӣ'},{en:'A crop with special water-management requirements. The exact technology depends on the variety and growing system.',ru:'Культура с особыми требованиями к управлению водным режимом. Конкретная технология зависит от сорта и системы выращивания.',tg:'Зироат бо талаботи махсус ба идоракунии низоми об. Технологияи дақиқ ба навъ ва низоми парвариш вобаста аст.'}),
 C('alfalfa','Medicago sativa','fodder','medium','perennial',P.green,{en:'Alfalfa',ru:'Люцерна',tg:'Беда'},{en:'A perennial fodder legume. It needs an assessment of drainage, acidity and water availability.',ru:'Многолетняя кормовая бобовая культура. Требует оценки дренажа, кислотности и доступности воды.',tg:'Лӯбиёгии бисёрсолаи хӯроквории чорво. Арзёбии дренаж, туршӣ ва дастрасии обро талаб мекунад.'}),
 C('sunflower','Helianthus annuus','oilseeds','medium','warm',P.field,{en:'Sunflower',ru:'Подсолнечник',tg:'Офтобпараст'},{en:'An oilseed crop; hybrid choice and sowing dates must match the temperature regime and season length.',ru:'Масличная культура, выбор гибрида и сроки посева должны соответствовать температурному режиму и длительности сезона.',tg:'Зироати равғандиҳанда; интихоби гибрид ва мӯҳлати кишт бояд ба низоми ҳарорат ва давомнокии мавсим мувофиқ бошад.'}),
 C('soybean','Glycine max','legumes','medium_high','warm',P.green,{en:'Soybean',ru:'Соя',tg:'Лӯбиёи соя'},{en:'A legume that depends strongly on maturity group and day length.',ru:'Бобовая культура, сильно зависящая от группы спелости и продолжительности светового дня.',tg:'Зироати лӯбиёгӣ, ки ба гурӯҳи пухтарасӣ ва дарозии рӯз сахт вобаста аст.'}),
 C('apple','Malus domestica','fruit','medium','perennial',P.veg,{en:'Apple',ru:'Яблоня',tg:'Себ'},{en:'A fruit crop. The variety’s winter chill requirement, frost risk and irrigation matter.',ru:'Плодовая культура. Важны зимняя холодовая потребность сорта, опасность заморозков и полив.',tg:'Зироати мевагӣ. Талаботи навъ ба сардии зимистона, хатари сармо ва обёрӣ муҳиманд.'}),
 C('apricot','Prunus armeniaca','fruit','medium','perennial',P.green,{en:'Apricot',ru:'Абрикос',tg:'Зардолу'},{en:'A fruit tree sensitive to spring frosts during flowering.',ru:'Плодовое дерево, чувствительное к весенним заморозкам во время цветения.',tg:'Дарахти мевадиҳанда, ки ба сармои баҳорӣ ҳангоми гулкунӣ ҳассос аст.'}),
 C('grape','Vitis vinifera','fruit','conditions','perennial',P.green,{en:'Grape',ru:'Виноград',tg:'Ангур'},{en:'A grapevine: the choice of variety, support and irrigation regime depends on heat supply and soil.',ru:'Виноградная лоза: выбор сорта, опоры и режима орошения зависит от теплообеспеченности и почвы.',tg:'Токи ангур: интихоби навъ, такягоҳ ва низоми обёрӣ аз таъминоти гармӣ ва хок вобаста аст.'}),
 C('chickpea','Cicer arietinum','legumes','low_medium','spring',P.wheat,{en:'Chickpea',ru:'Нут',tg:'Нахӯд'},{en:'A pulse crop. It needs an assessment of sowing dates, waterlogging risk and local diseases.',ru:'Зернобобовая культура. Нужна оценка сроков посева, риска переувлажнения и местных болезней.',tg:'Зироати лӯбиёгии донагӣ. Арзёбии мӯҳлати кишт, хатари обмонӣ ва бемориҳои маҳаллиро талаб мекунад.'})
];
export const cropName=c=>pick(c.names);
export const cropDesc=c=>pick(c.descs);
export const CATEGORIES=['cereals','vegetables','fruit','technical','fodder','oilseeds','legumes'];
// Demonstration priorities only: this is NOT agronomic suitability modelling or a verified ranking.
export const regionalDemos={
 'TJK-KHT':['cotton','wheat','corn','tomato','alfalfa','rice','grape','chickpea'],
 'TJK-SUG':['wheat','apricot','grape','tomato','apple','corn','potato'],
 'TJK-RRP':['wheat','tomato','grape','apple','alfalfa','corn'],
 'TJK-GBA':['barley','potato','wheat','apricot','alfalfa'],
 'USA-IA':['corn','soybean','alfalfa','wheat','oat'],
 'USA-KS':['wheat','corn','sunflower','soybean','alfalfa','chickpea'],
 'USA-NE-SC':['corn','soybean']
};
export const guideSteps=[1,2,3,4,5,6].map(i=>[`g${i}.t`,`g${i}.d`]);
