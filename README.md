# nether

*Nether means located beneath or below, lower or under.*

**nether je framework pro rychlé vytváření a nasazení webových služeb.**

Tento framwork vznikl z interních potřeba Wavelet.space, může ale nemusí vyhovovat tvým potřebám.
Našim cílem není vytvořit projektt, který bude vyhovovat všem, ale především nám!
Základnem je vyžít naplno standardní knihovnu; používat minimum externích balíku.

## Roadmap 

### 01

Nejdříve výtvoříme jádro knihovny, kdy naším cílem je spustit server, který umí
komunikovat přes HTTP. Server je schopen zaregistrovat další službu a komunikovat
s ní asynchrnonně. V této fázi nechceme řešit clean architecture ani domain driven design.

## Development notes

Problém: Neumíme zrušit běžící tasky, pokud zmáčkneme CTRL+C.

## Application

Na vrcholu hierarchie stojí třída `Application` ze které dědí každá aplikace postavená na knihovně Nether.

Application je centrální přístupový bod program. Applikace registruje služby, které mohou komunikovat interne i externě
přes aplikaci pomocí zpráv (publish/subscribe).
