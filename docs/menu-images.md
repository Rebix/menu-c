# Menu image sources

Source: [Lamiz coffee menu](https://lamizcoffee.com/lamiz-coffee-menu/). Retrieved on 2026-09-30.

The 16 original WebP files are stored in `public/images/menu/`. Astro copies these files into `dist/images/menu/` during the static build. The existing `wrangler.jsonc` deploys `dist/` as Cloudflare static assets. Image requests use local paths and do not contact Lamiz.

Drink cards serve 96 px images with 192 px alternatives for screens at 2x pixel density. Category tabs serve 64 px images with 128 px alternatives. The `srcset` attribute lets browsers select the appropriate image. The 38 variants use WebP quality 82 and retain the original composition. Drink photos load lazily and reserve their layout space with explicit dimensions.

The Persian menu titles, recipes, variants, and prices belong to this cafe. Lamiz names are recorded separately in `src/data/menu-image-sources.json`. Category images reuse espresso, iced latte, and black tea.

| Cafe item | Lamiz Persian name | Lamiz English name | Match | Local filename |
| --- | --- | --- | --- | --- |
| اسپرسو ۱۰۰٪ روبوستا | اسپرسو | Espresso | drink-family | espresso.webp |
| اسپرسو ۷۰/۳۰٪ روبوستا | اسپرسو | Espresso | drink-family | espresso.webp |
| اسپرسو ۵۰/۵۰٪ | اسپرسو | Espresso | drink-family | espresso.webp |
| اسپرسو ۱۰۰٪ عربیکا | اسپرسو | Espresso | drink-family | espresso.webp |
| اسپرسو لاین ویژه | اسپرسو | Espresso | drink-family | espresso.webp |
| لاته | کافه لاته | LATTE | equivalent | latte.webp |
| کاپوچینو | کپوچینو | CAPPUCCINO | equivalent | cappuccino.webp |
| آمریکانو | آمریکانو | AMERICANO | exact | americano.webp |
| قهوه فرانسه | قهوه دمی | Daily Brew | related | daily-brew.webp |
| موکا | کافه موکا | MOCHA | equivalent | mocha.webp |
| کارامل ماکیاتو | کارامل ماکیاتو | CARAMEL MACCHIATO | exact | caramel-macchiato.webp |
| هات چاکلت | شکلات گرم | HOT CHOCOLATE | equivalent | hot-chocolate.webp |
| ماسالا | ماسالا | MASALA | exact | masala.webp |
| هات چاکلت فندقی | No match |  | unmatched | No image |
| قهوه ترک | No match |  | unmatched | No image |
| آیس لاته | کافه لاته سرد | ICED LATTE | equivalent | iced-latte.webp |
| آیس آمریکانو | آمریکانو سرد | ICED AMERICANO | equivalent | iced-americano.webp |
| آیس موکا | کافه موکا سرد | ICED MOCHA | equivalent | iced-mocha.webp |
| آیس کارامل | کارامل ماکیاتو سرد | ICED CARAMEL MACCHIATO | assumed | iced-caramel-macchiato.webp |
| چای کرک | No match |  | unmatched | No image |
| چای ترش | دمنوش دم آشام ترش | Berry Hibiscus Sip | related | berry-hibiscus.webp |
| دم نوش چای سبز | چای سبز | green tea | equivalent | green-tea.webp |
| چای سیاه | چای سیاه لمیز | black tea | equivalent | black-tea.webp |

## Match limits

- `exact` and `equivalent` identify the same drink, including spelling and translated names.
- `drink-family` shares the espresso image across all five blends. Lamiz does not specify these blend ratios.
- French coffee uses the related Daily Brew image. Lamiz describes machine-brewed coffee, not French press.
- Hibiscus tea uses the related Berry Hibiscus Sip image. That Lamiz drink also contains fruit and quince tea.
- Iced caramel assumes the cafe means iced caramel macchiato. The cafe title alone does not confirm that recipe.
- Hazelnut hot chocolate, Turkish coffee, and karak tea have no matching drink on the supplied page. Their image fields remain empty, and the component omits their image slots.

## Script options

`python3 scripts/menu-images.py` verifies every mapping and local WebP file.

`python3 scripts/menu-images.py --download --optimize --apply` downloads missing originals, generates responsive variants, and applies reviewed image paths to the current menu data. Existing originals are reused. Downloads require network access and curl.

`python3 scripts/menu-images.py --optimize` regenerates the variants from the local originals. Optimization and build verification require Pillow, pinned in `scripts/requirements-images.txt`. The generated variants are included in the repository, so normal Astro builds and deployments do not require Python or Pillow.

`python3 scripts/menu-images.py --dist` verifies the rendered `srcset`, image dimensions, loading settings, and deployed image bytes. It reports the total image bytes at 1x and 2x pixel density. It requires a completed `pnpm build`.

`pnpm deploy` runs the build and then Wrangler using the existing Cloudflare configuration.
