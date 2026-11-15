// Coordinates are illustrative research-site locations, NOT verified field boundaries.
// No fabricated climate or soil measurements. All unknown metrics are null.
export const sites = [
 {id:'TJK-SUG-001',region:'TJK-SUG',lat:40.275,lon:69.635,area:null,crop:'wheat',soil:null,moisture:null,ndvi:null,ph:null,temp:null,regionalDemo:true},
 {id:'TJK-KHT-002',region:'TJK-KHT',lat:37.833,lon:68.782,area:null,crop:'cotton',soil:null,moisture:null,ndvi:null,ph:null,temp:null,regionalDemo:true},
 {id:'TJK-DRS-003',region:'TJK-RRP',lat:38.526,lon:68.563,area:null,crop:'wheat',soil:null,moisture:null,ndvi:null,ph:null,temp:null,regionalDemo:true},
 {id:'TJK-GBA-004',region:'TJK-GBA',lat:37.49,lon:71.55,area:null,crop:'barley',soil:null,moisture:null,ndvi:null,ph:null,temp:null,regionalDemo:true},
 {id:'TJK-SUG-005',region:'TJK-SUG',lat:39.91,lon:69.0,area:null,crop:'veg',soil:null,moisture:null,ndvi:null,ph:null,temp:null,regionalDemo:true},
 {id:'USA-IA-001',region:'USA-IA',lat:42.05,lon:-93.6,area:null,crop:'corn',soil:null,moisture:null,ndvi:null,ph:null,temp:null},
 {id:'USA-KS-002',region:'USA-KS',lat:38.5,lon:-98.2,area:null,crop:'wheat',soil:null,moisture:null,ndvi:null,ph:null,temp:null},
 {id:'USA-NE-SCAL',region:'USA-NE-SC',lat:40.575256,lon:-98.137824,area:null,crop:'corn',soil:null,moisture:null,ndvi:null,ph:null,temp:null,referenceOnly:true}
];
// Crop key -> unsplash illustration (analog photos, not verified photos of the sites)
export const sitePhotos={
 wheat:['https://images.unsplash.com/photo-1501436513145-30f24e19fcc4?w=1200&q=80','https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=1000&q=80'],
 cotton:['https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&q=80','https://images.unsplash.com/photo-1620200423727-8127f75d7f53?w=1000&q=80'],
 corn:['https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&q=80','https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1000&q=80'],
 barley:['https://images.unsplash.com/photo-1501436513145-30f24e19fcc4?w=1200&q=80'],
 veg:['https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1200&q=80']};
export const photoFallback='https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&q=80';

// No verified cadastral boundaries are bundled with the prototype.
// A small illustrative polygon is generated around each sample point and always labelled DEMO.
export function demoFieldPolygon(site){
 const dx=0.009, dy=0.0055, x=site.lon, y=site.lat;
 return {type:'Feature',properties:{site_id:site.id,source_type:'demo',verified:false},geometry:{type:'Polygon',coordinates:[[[x-dx,y-dy],[x+dx,y-dy*0.8],[x+dx*0.85,y+dy],[x-dx*0.8,y+dy*0.9],[x-dx,y-dy]]]}};
}
