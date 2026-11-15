# Public crop images (GitHub / static deployment)

For each crop create `assets/crops/<crop-id>/card.webp`, `detail.webp`, and `background.webp`.
Then edit `js/crop-images.js` and set each path separately, e.g.:

```js
corn: {card:'./assets/crops/corn/card.webp', detail:'./assets/crops/corn/detail.webp', background:'./assets/crops/corn/background.webp'},
```

Card: square ~800x800. Detail: landscape/portrait ~1400x1000. Background: landscape ~1920x1080.
Recommended WebP; only upload images you have rights to publish. Commit images and manifest to Git.
GitHub Pages cannot save browser uploads. For uploads via browser, use a writable server with admin authentication and persistent storage; cloud-demo deliberately disables uploads.
