# Nether

*Nether means located beneath or below, lower or under.*

**nether je framework pro rychlé vytváření a nasazení webových služeb.**

Tento framework vznikl z interních potřeba <https://arjuna.group>, může ale nemusí vyhovovat tvým potřebám.
Našim cílem není vytvořit projektt, který bude vyhovovat všem, ale především nám!
Základnem je vyžít naplno standardní knihovnu; používat minimum externích balíku.

## Požadavky

Naše představa, co by měl tento framework umožňovat a splňovat:

- Uživatel by měl být schopný nastartovat aplikační server a vybrat (registrovat) vybrané služby. Tyto služby mohou být součástí tohoto frameworku, např. webpage služba může servírovat HTML stránky, WebSocket služba umožňuje komunikovat se serverem pomocí webových socketů, autentizační služba umožnuje ověřit oprávnění před použitím jiné služby.
- Uživatel by také měl bých schopný spustit jednoduše službu zpracovávjíci úlohy na pozadí (background processing) ve stanovéném intervalu nebo načasování (scheduled). Nakonec všechny služby by měli být schopné komunikovat pomocí zpráv přes zabudovaný publish-subscribe mechanizmus pomocí mediátoru (message-bus).
- Důležitým požadavkem je, že selhání jakékoliv služby neshodí celou aplikaci. To jak služba ošetřuje chybové stavy je její záležitost a v nejhorším případě může informovat aplikaci o neošetřitelném stavu. Aplikace se pak může rozhodnout, jak bude reagovat.
- Aplikace by měla zpracovávat požadavky asychronně tj. neblokujícím způsobem IO operace a zároveň umožňovat efektivně spouštět CPU intenzivní úlohy (zřejmě na vláknech).
- Nesmí docházek k tomu, že se spouští vlákna, která nelze jednoduše monitorovat a případně ukončit.

Problém: Neumíme zrušit běžící tasky, pokud zmáčkneme CTRL+C.

## Architektura

### Application

Na vrcholu hierarchie stojí třída `Application` ze které dědí každá aplikace postavená na knihovně Nether.

Application je centrální přístupový bod program. Applikace registruje služby, které mohou komunikovat interne i externě
přes aplikaci pomocí zpráv (publish/subscribe).

## Roadmap

### 01

Nejdříve výtvoříme jádro knihovny, kdy naším cílem je spustit server, který umí
komunikovat přes HTTP. Server je schopen zaregistrovat další službu a komunikovat
s ní asynchrnonně. V této fázi nechceme řešit clean architecture ani domain driven design.
