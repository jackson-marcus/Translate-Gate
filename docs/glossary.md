# BrandCo Localization Glossary & Style Rules

## term-checkout
EN "checkout" must be translated as "kassa". Never use "zahlung" or "bezahlung" — those are reserved for payment-method contexts. Checkout refers to the flow, not the transaction.

## term-cart
EN "cart" must be translated as "korv". The legacy term "wagen" was retired in 2024 and must not appear in new strings.

## term-account
EN "account" must be translated as "konto". Do not use "profil" — profile refers only to the public-facing page.

## term-subscription
EN "subscription" must be translated as "abonnemang". The shortened "abo" is acceptable only in space-constrained UI (under 20 characters).

## term-order
EN "order" (noun) must be translated as "beställning". As a verb, use "beställa". Never "kommando", which is a command in the technical sense.

## term-refund
EN "refund" must be translated as "återbetalning". Do not use "retur" — that is a return of goods, not money.

## term-shipping
EN "shipping" must be translated as "frakt". "Leverans" means delivery (the event), not shipping (the service).

## term-settings
EN "settings" must be translated as "inställningar". Never leave it in English, even in developer-facing strings.

## brand-names
"BrandCo", "BrandCo Pro" and "BrandCo Premium" are NEVER translated or declined. They keep exact casing in every locale.

## placeholders
Placeholders like {name}, {count}, %s and %d must appear in the target exactly as many times as in the source, unmodified. Reordering is allowed; renaming or dropping is a release blocker.

## length-budget
Target strings should stay within 0.6x-1.9x of the source length. Buttons and labels above that range risk truncation; below it, information was probably lost.

## tone
Use informal second person throughout. No exclamation marks in error messages. Numbers, dates and currency symbols follow the locale, but the VALUES must match the source exactly.
