# Almere OCR

Gratis OCR proefomgeving voor openbare NotuBiz documenten van de gemeente Almere.

## Status

De eerste workflow is **uitsluitend handmatig te starten**. Hij verwerkt één pagina van een vast openbaar testdocument (Supabase document 28301) op een GitHub Linux runner met Tesseract en Poppler. De standaardtest is pagina 387 op 300 DPI.

* De bestaande Supabase productieomgeving en OCR wachtrij worden niet gewijzigd.
* Er worden geen Supabase toegangssleutels gebruikt.
* Er wordt geen tekst naar Supabase geschreven.
* Geen PDF, afbeelding of OCR tekst wordt naar GitHub artifacts of logs geüpload.
* Alleen aantallen herkende woorden, tekens en OCR betrouwbaarheidsstatistieken verschijnen in het joboverzicht.
* OCR vertrouwensscores zijn **geen** objectieve kwaliteitsmeting. Controleer inhoud en kolomvolgorde afzonderlijk.

## Test uitvoeren

Open de [workflow](https://github.com/rkleinsmit-cmd/almere-ocr/actions/workflows/ocr-probe.yml), kies **Run workflow**, gebruik pagina `387` en DPI `300`. Na afloop staat een statistisch overzicht in de job summary.

## Vervolg

Voor aansluiting op de Supabase wachtrij is een afzonderlijk beveiligd uitgifte en ontvangstprotocol nodig met afgebakende rechten, tijdelijke taakreservering, idempotente opslag, kwaliteitscontroles en een beperkte hoeveelheid taken per uitvoering. Publiceer nooit een Supabase service role sleutel of documentinhoud in een openbare repository of Actions log.

Dit project is momenteel een **read-only proof of concept**.
