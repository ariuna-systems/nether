# Nether

**Nether je framework pro vytváření serverových služeb.**

*Nether means located beneath or below, lower or under.*

Tento framework vznikl z interních potřeb <https://arjuna.group> pro vytváření modulárních serverových aplikací. Základním principem je naplno vuyžívat standardní knihovnu a používat minimum externích balíků z důvodu možnosti nasazení v regulovaných prostředích. Aplikace lze rozšiřovat pomocí vlastních extenzí, které se registrují při jejím startu a mohou komunikovat s dalšími částmi systému pomocí zasílání zpráv (*publish-subsribe*),

## Roadmap

Nejdříve výtvoříme jádro knihovny, kdy naším cílem je spustit server, který umí
komunikovat přes HTTP. Server je schopen zaregistrovat další službu a komunikovat
s ní asynchrnonně. V této fázi nechceme řešit clean architecture ani domain driven design.

## Dokumentace

### Požadavky

Naše představa, co by měl tento framework umožňovat a splňovat:

- Uživatel může spustit aplikační server a registrovat vybrané služby. Tyto služby mohou být součástí tohoto frameworku, např. webpage služba může servírovat HTML stránky, WebSocket služba umožňuje komunikovat se serverem pomocí webových socketů, autentizační služba umožnuje ověřit oprávnění před použitím jiné služby.
- Uživatel by také měl bých schopný spustit jednoduše službu zpracovávjíci úlohy na pozadí (background processing) ve stanovéném intervalu nebo načasování (scheduled). Nakonec všechny služby by měli být schopné komunikovat pomocí zpráv přes zabudovaný publish-subscribe mechanizmus pomocí mediátoru (message-bus).
- Důležitým požadavkem je, že selhání jakékoliv služby neshodí celou aplikaci. To jak služba ošetřuje chybové stavy je její záležitost a v nejhorším případě může informovat aplikaci o neošetřitelném stavu. Aplikace se pak může rozhodnout, jak bude reagovat.
- Aplikace by měla zpracovávat požadavky asychronně tj. neblokujícím způsobem IO operace a zároveň umožňovat efektivně spouštět CPU intenzivní úlohy (zřejmě na vláknech).
- Nesmí docházek k tomu, že se spouští vlákna, která nelze jednoduše monitorovat a případně ukončit.

Problém: Neumíme zrušit běžící tasky, pokud zmáčkneme CTRL+C.

### Architektura

#### Application

Na vrcholu hierarchie stojí třída `Application` ze které dědí každá aplikace postavená na knihovně Nether.

Application je centrální přístupový bod program. Applikace registruje služby, které mohou komunikovat interne i externě
přes aplikaci pomocí zpráv (publish/subscribe).
