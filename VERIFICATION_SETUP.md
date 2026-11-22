# Almere feitencontrole: aansluitvoorwaarden

Status: **niet operationeel**. De handmatige pilot in `.github/workflows/verification-pilot.yml` is fail closed en kan nog geen dossier afronden. Activeer geen periodieke uitvoering.

## Vereiste GitHub Actions Secrets

1. `ALMERE_DATABASE_URL`: afzonderlijke PostgreSQL verbinding met uitsluitend benodigde rechten op `signal_radar`, `public.storage_work_permit` en de veiligheidsstatus. Gebruik geen Supabase service role sleutel in deze publieke repository.
2. `GROQ_API_KEY`: persoonlijke sleutel voor de gratis Groq API. Stel bij de aanbieder een bestedingslimiet in en controleer het actuele gratis quotum.

Instellen: repository > Settings > Secrets and variables > Actions > New repository secret. Deel sleutels niet in de chat.

## Nog te bouwen voordat de eerste productieclaim is toegestaan

* Lees bestaande bewijsnotities en relevante duplicaatkandidaten.
* Verzamel originele bron en primaire raadsdocumenten via geverifieerde vindplaatsen. Raadpleeg bij relevante dossiers besluiten, moties, toezeggingen en uitvoering. Markeer ontbrekende onderdelen als niet gecontroleerd.
* Leg per conclusie concrete bron URL, documentidentificatie, publicatiedatum en ondersteunend tekstfragment vast. Het model mag niet zelf controlemarkeringen toekennen.
* Controleer duplicaten deterministisch op artikelidentificatie, genormaliseerde URL en bestaande databasegegevens.
* Beperk externe webverzoeken tegen SSRF, redirects naar privé IP adressen en buitensporige downloads.
* Zorg dat iedere mutatie vooraf een verse storage permit en safety check uitvoert. Bestaande SQL functies controleren dit ook intern.
* Verifieer na `briefing_finalize` dat status, classificatie, bewijs en vrijgave van lease werkelijk zijn opgeslagen.
* Zorg voor afhandeling van verlopen leases, rate limits, uitzonderingen en uitval zonder onterechte complete claims.
* Maak een integratietest met tien unieke dossiers, inclusief simulatie van uitval, vóór activering van een schema.

## Belangrijk

De huidige pilot vraagt een AI beoordeling op basis van slechts één HTML bron. Dit is **niet voldoende** voor volledige feitencontrole. Daarom is de opslag via `briefing_finalize` bewust uitgeschakeld. Ook een handmatige uitvoering met werkende secrets levert nog geen afgerond dossier op. Het is onjuist om deze pilot als productiegeschikt te beschouwen.
