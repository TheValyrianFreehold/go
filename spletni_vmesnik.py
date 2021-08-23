import bottle
import model

PISKOTEK_UPORABNISKO_IME = "uporabnisko_ime"
SKRIVNOST = "polinomi so stevila"

class Odigrano(Exception): pass

def trenutni_uporabnik():
    uporabnisko_ime = bottle.request.get_cookie(
        PISKOTEK_UPORABNISKO_IME, secret = SKRIVNOST
    )
    if uporabnisko_ime:
        return model.Uporabnik.iz_datoteke(uporabnisko_ime)

@bottle.get("/")
def zacetna_stran():
	return bottle.template("home.html", uporabnik = trenutni_uporabnik())

@bottle.get("/stare_igre/")
def stare_igre():
	return bottle.template("stare_igre.html", uporabnik = trenutni_uporabnik())

@bottle.get("/pravila/")
def pravila():
	return bottle.template("pravila.html", uporabnik = trenutni_uporabnik())

@bottle.get("/prijava/")
def prijava():
	return bottle.template("prijava.html", uporabnik = trenutni_uporabnik(), napaka = None)

@bottle.post("/prijava/")
def prijava_post():
	uporabnikso_ime = bottle.request.forms.getunicode("uporabnisko_ime")
	geslo = bottle.request.forms.getunicode("geslo")
	if not uporabnikso_ime:
		return bottle.template("prijava.html", napaka = "Vnesi uporabniško ime!", uporabnik = trenutni_uporabnik())
	if not geslo:
		return bottle.template("prijava.html", napaka = "Vnesi geslo!", uporabnik = trenutni_uporabnik())
	try:
		model.Uporabnik.prijava(uporabnikso_ime, geslo)
		bottle.response.set_cookie(PISKOTEK_UPORABNISKO_IME, uporabnikso_ime, path = "/", secret = SKRIVNOST)
		bottle.redirect("/")
	except ValueError as e:
		return bottle.template("prijava.html", napaka=e.args[0], uporabnik = trenutni_uporabnik())

@bottle.get("/registracija/")
def registracija():
	return bottle.template("registracija.html", uporabnik = trenutni_uporabnik(), napaka = None)

@bottle.post("/registracija/")
def registracija_post():
	uporabnisko_ime = bottle.request.forms.getunicode("uporabnisko_ime")
	geslo_1 = bottle.request.forms.getunicode("geslo1")
	geslo_2 = bottle.request.forms.getunicode("geslo2")
	if not uporabnisko_ime:
		return bottle.temple("registracija.html", napaka = "Vnesi uporabniško ime!", uporabnik = trenutni_uporabnik())
	if not geslo_1:
		return bottle.template("registracija.html", napaka = "Vnesi geslo!", uporabnik = trenutni_uporabnik())
	if geslo_1 != geslo_2:
		return bottle.template("registracija.html", napaka = "Gesli se ne ujemata!", uporabnik = trenutni_uporabnik())
	try:
		model.Uporabnik.registracija(uporabnisko_ime, geslo_1)
		bottle.response.set_cookie(PISKOTEK_UPORABNISKO_IME, uporabnisko_ime, path = "/", secret = SKRIVNOST)
		bottle.redirect("/")
	except ValueError as e:
		return bottle.template("registracija.html", napaka=e.args[0], uporabnik = trenutni_uporabnik())

@bottle.get("/odjava/")
def odjava():
    bottle.response.delete_cookie(PISKOTEK_UPORABNISKO_IME, path = "/")
    bottle.redirect("/")

@bottle.get("/igra/<id:int>")
def trenutna(id):
	uporabnik = trenutni_uporabnik()
	igra = uporabnik.igre[id]
	if bottle.request.query.x:
		x = int(bottle.request.query.x)
		y = int(bottle.request.query.y)
		menjaj = bottle.request.query.menjaj
		barva = bottle.request.query.izbrana_barva
		stevilo = igra.velikost * x + y
		try:
			igra.Odigraj_potezo(stevilo, barva)
		except Odigrano: pass
	else:
		barva = model.CRNA
		menjaj = "True"
	uporabnik.v_datoteko()
	if menjaj == "True" and len(igra.stare_plosce) != 0:
		naslednje = (model.BELA if igra.stare_plosce[-1][1] == model.CRNA else model.CRNA)
	else:
		naslednje = barva
	return bottle.template(
		"igra.html", id = id, igra = igra, izbrano = naslednje, menjaj = menjaj, uporabnik = trenutni_uporabnik()
		)

@bottle.get("/stare_poteze/<id:int>/<poteza>")
def prejsnja(id, poteza):
	uporabnik = trenutni_uporabnik()
	igra = uporabnik.igre[id]
	poteza = int(poteza)
	return bottle.template(
		"stare_poteze.html", id = id, igra = igra, poteza = poteza, uporabnik = trenutni_uporabnik()
		)

@bottle.get("/igra/<id:int>/<izbor>")
def trenutna_barva(id, izbor):
	uporabnik = trenutni_uporabnik()
	igra = uporabnik.igre[id]
	if izbor == "True":
		menjaj = izbor
		if len(igra.stare_plosce) != 0:
			barva = (model.BELA if igra.stare_plosce[-1][1] == model.CRNA else model.CRNA)
		else:
			barva = model.CRNA
	else:
		menjaj = "False"
		barva = izbor
	print(barva)
	return bottle.template(
		"igra.html", id = id, igra = igra, izbrano = barva, menjaj = menjaj, uporabnik = trenutni_uporabnik()
		)

@bottle.get("/brisi/<id:int>")
def brisi(id):
	uporabnik = trenutni_uporabnik()
	del uporabnik.igre[id]
	uporabnik.v_datoteko()
	bottle.redirect(f"/stare_igre/")

@bottle.get("/nastavitve/")
def nastavitve():
	if trenutni_uporabnik() == None: bottle.redirect("/prijava/")
	return bottle.template("nastavitve.html", napaka = None, uporabnik = trenutni_uporabnik())

@bottle.post("/nastavitve/")
def nastavitve_post():
	niz = bottle.request.forms.getunicode('velikost')
	if not niz:
		niz = 19
	else:
		niz = int(niz)
	uporabnik = trenutni_uporabnik()
	if niz > 19 or niz < 1:
		return bottle.template("nastavitve.html", napaka = "Neveljavna velikost!", uporabnik = trenutni_uporabnik())
	id = uporabnik.nova_igra(niz)
	uporabnik.v_datoteko()
	bottle.redirect(f"/igra/{id}")

@bottle.get("/img/<picture>")
def slike(picture):
	return bottle.static_file(picture, "img")
	
bottle.run(reloader=True, debug=True)