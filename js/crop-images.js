/* Crop media stored in Git: put files in assets/crops/<id>/ and edit entries.
   All paths must be same-origin project assets. Three independent slots:
   card (catalog), detail (large crop portrait), background (full-page background).
   A blank entry uses existing project defaults. No personal data or license claims. */
export const CROP_MEDIA = {
  wheat:    {card:'', detail:'', background:''},
  cotton:   {card:'', detail:'', background:''},
  corn:     {card:'', detail:'', background:''},
  barley:   {card:'', detail:'', background:''},
  tomato:   {card:'', detail:'', background:''},
  potato:   {card:'', detail:'', background:''},
  rice:     {card:'', detail:'', background:''},
  alfalfa:  {card:'', detail:'', background:''},
  sunflower:{card:'', detail:'', background:''},
  soybean:  {card:'', detail:'', background:''},
  apple:    {card:'', detail:'', background:''},
  apricot:  {card:'', detail:'', background:''},
  grape:    {card:'', detail:'', background:''},
  chickpea: {card:'', detail:'', background:''},
};
export const mediaFor = (id,slot) => CROP_MEDIA[id]?.[slot] || '';
