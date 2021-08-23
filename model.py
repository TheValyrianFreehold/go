import hashlib
import json
import random

BELA, CRNA, PRAZNO = "W", "B", "p"

class Uporabnik:
    def __init__(self, uporabnisko_ime, zasifrirano_geslo, igre = dict({})):
        self.uporabnisko_ime = uporabnisko_ime
        self.zasifrirano_geslo = zasifrirano_geslo
        self.igre = igre
    
    @staticmethod
    def prijava(uporabnisko_ime, geslo_v_cistopisu):
        uporabnik = Uporabnik.iz_datoteke(uporabnisko_ime)
        if uporabnik is None:
            raise ValueError("Uporabniško ime ne obstaja!")
        elif uporabnik.preveri_geslo(geslo_v_cistopisu):
            return uporabnik        
        else:
            raise ValueError("Geslo je napačno!")

    @staticmethod
    def registracija(uporabnisko_ime, geslo_v_cistopisu):
        if Uporabnik.iz_datoteke(uporabnisko_ime) is not None:
            raise ValueError("Uporabniško ime že obstaja!")
        else:
            zasifrirano_geslo = Uporabnik._zasifriraj_geslo(geslo_v_cistopisu)
            uporabnik = Uporabnik(uporabnisko_ime, zasifrirano_geslo)
            uporabnik.v_datoteko()
            return uporabnik

    def _zasifriraj_geslo(geslo_v_cistopisu, sol=None):
        if sol is None:
            sol = str(random.getrandbits(32))
        posoljeno_geslo = sol + geslo_v_cistopisu
        h = hashlib.blake2b()
        h.update(posoljeno_geslo.encode(encoding="utf-8"))
        return f"{sol}${h.hexdigest()}"

    def v_slovar(self):
        return {
            "uporabnisko_ime": self.uporabnisko_ime,
            "zasifrirano_geslo": self.zasifrirano_geslo,
            "igre": {id : self.igre[id].v_slovar() for id in self.igre}
        }

    def v_datoteko(self):
        with open(
            Uporabnik.ime_uporabnikove_datoteke(self.uporabnisko_ime), "w"
        ) as datoteka:
            json.dump(self.v_slovar(), datoteka, ensure_ascii=False, indent=4)

    def preveri_geslo(self, geslo_v_cistopisu):
        sol, _ = self.zasifrirano_geslo.split("$")
        return self.zasifrirano_geslo == Uporabnik._zasifriraj_geslo(geslo_v_cistopisu, sol)

    @staticmethod
    def ime_uporabnikove_datoteke(uporabnisko_ime):
        return f"{uporabnisko_ime}.json"

    @staticmethod
    def iz_slovarja(slovar):
        uporabnisko_ime = slovar["uporabnisko_ime"]
        zasifrirano_geslo = slovar["zasifrirano_geslo"]
        uporabnik = Uporabnik(uporabnisko_ime, zasifrirano_geslo)
		
        uporabnik.igre = {int(id) : Igra.iz_slovarja(slovar["igre"][id]) for id in slovar["igre"]}
        return uporabnik

    @staticmethod
    def iz_datoteke(uporabnisko_ime):
        try:
            with open(Uporabnik.ime_uporabnikove_datoteke(uporabnisko_ime)) as datoteka:
                slovar = json.load(datoteka)
                return Uporabnik.iz_slovarja(slovar)
        except FileNotFoundError:
            return None

    def prost_id_igre(self):
        return len(self.igre)
    
    def nova_igra(self, velikost):
        id = self.prost_id_igre()
        self.igre[id] = Igra(velikost, PRAZNO * (velikost ** 2))
        return id
    

class Igra:
    def __init__(self, velikost: int, plosca: str, stare_plosce = [], pobrani = {BELA : 0, CRNA : 0}) -> None:
        """
        Ploščo predstavimo z nizom dolžine n*n, 
        kjer je n velikost plošče in kjer i-ta n-terica zankov predstavlja i-to vrstico plošče.
        """
        self.velikost = velikost
        self.plosca = plosca
        self.stare_plosce = stare_plosce
        self.pobrani = pobrani

    @staticmethod
    def iz_slovarja(slovar: dict):
        igra = Igra(int(slovar["velikost"]), slovar["plosca"], slovar["stare_plosce"], slovar["pobrani"])
        return igra

    def v_slovar(self) -> dict:
        return {
			"velikost" : self.velikost,
			"stare_plosce" : self.stare_plosce,
			"pobrani" : self.pobrani,
            "plosca" : self.plosca
		}

    def Koordinate_v_stevilo(self, koordinate) -> int:
        "Spremeni koordinate oblike (x, y) v število, ki jim pripada."
        return self.velikost * koordinate[0] + koordinate[1]

    def Stevilo_v_koordinate(self, stevilo: int) -> tuple:
        "Spremeni število v koordinate, ki mu pripadajo."
        return divmod(stevilo, self.velikost)

    def Veljavne_koordinate(self, koordinate)  -> bool:
        "Preveri, da koordinate ležijo na plošči."
        return (koordinate[0] % self.velikost == koordinate[0] and koordinate[1] % self.velikost == koordinate[1])
    
    def Poisci_sosede(self, stevilo: int) -> list:
        """
        Poišče sosednje koordinate števila na plošči, 
        pri čemer ignorira neveljavne koordinate (ne 'pademo' čez rob plošče).
        """
        x, y = self.Stevilo_v_koordinate(stevilo)
        mozni_sosednje = ((x+1, y), (x-1, y), (x, y+1), (x, y-1))
        return [self.Koordinate_v_stevilo(n) for n in mozni_sosednje if self.Veljavne_koordinate(n)]

    def Doseg(self, polje: int):
        """
        Funkcija vrne največjo skupino povezanih polj, 
        na katerih so kamni iste barve kot na vhodnem polju (veriga), 
        ter koordinate mejnih polj te skupine (doseg).
        """
        barva = self.plosca[polje]
        veriga = set([polje])
        doseg = set()
        meja = [polje]
        while meja:
            trenutno_polje = meja.pop()
            veriga.add(trenutno_polje)
            for sosed in self.Poisci_sosede(trenutno_polje):
                if self.plosca[sosed] == barva and not sosed in veriga:
                    meja.append(sosed)
                elif self.plosca[sosed] != barva:
                    doseg.add(sosed)
        return veriga, doseg
    
    def Igraj_kamen(self, barva: str, poteza: int) -> str:
        "Na mesto poteze zapiše barvo."
        return self.plosca[:poteza] + barva + self.plosca[poteza + 1:]
    
    def Vecja_sprememba(self, barva: str, polja: list) -> str:
        "Več polj prebarva v novo barvo."
        bitna_plosca = bytearray(self.plosca, encoding="ascii")
        barva = ord(barva)
        for kamen in polja:
            bitna_plosca[kamen] = barva
        return bitna_plosca.decode('ascii')

    def Poberi_obkrozene(self, poteza: int):
        "Pobere kamne, ki so obkoljeni, če obstajajo."
        veriga, doseg = self.Doseg(poteza)
        if not any(self.plosca[polje] == PRAZNO for polje in doseg):
            pobrani = self.plosca[list(veriga)[0]]
            self.plosca = self.Vecja_sprememba(PRAZNO, veriga)
            return self.plosca, veriga, pobrani
        return self.plosca, [], None

    def Odigraj_potezo(self, poteza: int, barva: str) -> str:
        """
        Odigra potrebno potezo, pri čemer ločeno obravnava brisanje kamnov,
        nato pa iz plošče pobere obkrožene kamne.
        """
        if barva == PRAZNO:
            self.stare_plosce.append((self.plosca, self.plosca[poteza]))
            self.plosca = self.Igraj_kamen(barva, poteza)
            return self.plosca
        self.stare_plosce.append((self.plosca, barva))
        self.plosca = self.Igraj_kamen(barva, poteza)
        druga_barva = (BELA if barva == CRNA else CRNA)
        drugi_kamni = []
        moji_kamni = []
        for polje in self.Poisci_sosede(poteza):
            if self.plosca[polje] == barva:
                moji_kamni.append(polje)
            elif self.plosca[polje] == druga_barva:
                drugi_kamni.append(polje)
        verige = []
        moji_kamni.append(poteza)
        for kamen in drugi_kamni:
            self.plosca, veriga, pobrani = self.Poberi_obkrozene(kamen)
            if veriga not in verige:
                if pobrani != None:
                    self.pobrani[pobrani] += len(veriga)
                verige.append(veriga)
        verige = []
        for kamen in moji_kamni:
            self.plosca, veriga, pobrani = self.Poberi_obkrozene(kamen)
            if veriga not in verige:
                if pobrani != None:
                    self.pobrani[pobrani] += len(veriga)
                verige.append(veriga)

        return self.plosca

    def Prestej_tocke(self) -> float:
        """
        Vsaki barvi priredi pripadajoče število točk; 
        prazno križišče pripada barvi, če ne more doseči nasprotne barve.
        """
        while PRAZNO in self.plosca:
            prazno_polje = self.plosca.index(PRAZNO)
            prazni, meje = self.Doseg(prazno_polje)
            mozna_barva = self.plosca[list(meje)[0]]
            if all(self.plosca[polje] == mozna_barva for polje in meje):
                self.plosca = self.Vecja_sprememba(mozna_barva, prazni)
            else:
                self.plosca = self.Vecja_sprememba("?", prazni)
        tocke = self.plosca.count(CRNA) + self.pobrani[BELA]- self.plosca.count(BELA) - self.pobrani[CRNA] - 7.5
        return tocke