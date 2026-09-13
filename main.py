import requests
import threading
import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Window.clearcolor = (0.05, 0.05, 0.06, 1)

class TarjetaPronostico(BoxLayout):
    def __init__(self, datos, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 360 # Tarjeta alta para evitar encimados
        self.padding = 15
        self.spacing = 10 
        
        with self.canvas.before:
            Color(0.12, 0.13, 0.16, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[15])
        self.bind(size=self.actualizar_fondo, pos=self.actualizar_fondo)
        
        # Textos separados de forma segura para evitar errores al copiar
        t_head = f"[color=#A0A0A0]{datos['liga']}  |  {datos['hora']}[/color]"
        lbl_header = Label(text=t_head, markup=True, font_size='13sp')
        
        t_eq = f"[b][color=#FFFFFF]{datos['local']} VS {datos['visita']}[/color][/b]"
        lbl_equipos = Label(text=t_eq, markup=True, font_size='18sp', halign='center', valign='middle')
        lbl_equipos.bind(size=lambda instance, size: setattr(instance, 'text_size', (size[0]-20, None)))
        
        t_pick = (
            f"[color=#00E5FF]{datos['mercado']}[/color]\n"
            f"[b][color=#00FF40]PICK: {datos['pick']}[/color][/b]\n"
            f"[b][color=#FFD700]CUOTA SUGERIDA: {datos['cuota_pick']}[/color][/b]"
        )
        lbl_pick = Label(text=t_pick, markup=True, font_size='16sp', halign='center', valign='middle')
        lbl_pick.bind(size=lambda instance, size: setattr(instance, 'text_size', (size[0]-10, None)))
        
        t_prob = f"[color=#AAAAAA]Probabilidad:[/color] L({datos['prob_h']}) | E({datos['prob_d']}) | V({datos['prob_a']})"
        lbl_prob = Label(text=t_prob, markup=True, font_size='13sp')
        
        t_cuotas = f"[b][color=#AAAAAA]1X2:[/color] L: [color=#00FF40]{datos['c_1']}[/color]  |  E: [color=#00FF40]{datos['c_x']}[/color]  |  V: [color=#00FF40]{datos['c_2']}[/color][/b]"
        lbl_cuotas = Label(text=t_cuotas, markup=True, font_size='14sp')

        self.add_widget(lbl_header)
        self.add_widget(lbl_equipos)
        self.add_widget(lbl_pick)
        self.add_widget(lbl_prob)
        self.add_widget(lbl_cuotas)

    def actualizar_fondo(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class TuPronosticosApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=15)
        
        self.titulo = Label(text="[b][color=#FFD700]TU PRONOSTICOS[/color][/b]", markup=True, font_size='28sp', size_hint_y=None, height=45)
        self.root.add_widget(self.titulo)
        
        # BOTON GIGANTE
        self.btn_cargar = Button(
            text="BUSCAR PRONOSTICOS", 
            background_normal='', background_color=(0.05, 0.75, 0.25, 1), 
            size_hint_y=None, height=80, 
            size_hint_x=1, 
            bold=True, font_size='22sp'
        )
        self.btn_cargar.bind(on_release=self.iniciar_busqueda)
        self.root.add_widget(self.btn_cargar)
        
        self.estado = Label(text="", size_hint_y=None, height=25, color=(0.7, 0.7, 0.7, 1))
        self.root.add_widget(self.estado)
        
        self.scroll = ScrollView(size_hint=(1, 1))
        self.lista_partidos = GridLayout(cols=1, spacing=20, size_hint_y=None)
        self.lista_partidos.bind(minimum_height=self.lista_partidos.setter('height'))
        
        self.scroll.add_widget(self.lista_partidos)
        self.root.add_widget(self.scroll)
        
        return self.root

    def iniciar_busqueda(self, instance):
        self.lista_partidos.clear_widgets()
        self.estado.text = "Analizando solo cuotas mayores a 1.50..."
        self.btn_cargar.disabled = True
        threading.Thread(target=self.obtener_datos_reales).start()

    def obtener_datos_reales(self):
        try:
            headers = {
                'x-rapidapi-host': "v3.football.api-sports.io",
                'x-rapidapi-key': "769a8efdc3789fad5ab1864f75b4ff78"
            }
            hoy = datetime.datetime.now().strftime("%Y-%m-%d")
            
            params_fix = {"date": hoy, "status": "NS", "timezone": "America/Mexico_City"}
            res_fix = requests.get("https://v3.football.api-sports.io/fixtures", headers=headers, params=params_fix, verify=False, timeout=12)
            datos_f = res_fix.json()
            
            if not datos_f.get('response'):
                Clock.schedule_once(lambda dt: self.actualizar_estado("No hay mas partidos programados para hoy."))
                return
            
            ligas_top = [39, 140, 135, 78, 61, 262, 253, 71, 128, 2, 3, 11, 13, 29, 255] 
            partidos_filtrados = [p for p in datos_f['response'] if p['league']['id'] in ligas_top]
            
            if not partidos_filtrados:
                partidos_filtrados = datos_f['response']
            
            resultados_ui = []
            
            for p in partidos_filtrados:
                if len(resultados_ui) >= 8:
                    break 
                
                fix_id = p['fixture']['id']
                hora_sola = p['fixture']['date'].split('T')[1][:5]
                
                res_pred = requests.get("https://v3.football.api-sports.io/predictions", headers=headers, params={"fixture": fix_id}, verify=False, timeout=8)
                datos_p = res_pred.json()
                
                if not datos_p.get('response'):
                    continue
                
                pred = datos_p['response'][0]['predictions']
                val_h = int(pred['percent']['home'].replace('%', ''))
                val_a = int(pred['percent']['away'].replace('%', ''))
                
                c_1, c_x, c_2 = "-", "-", "-"
                c_over25, c_btts = "-", "-"
                
                try:
                    res_odds = requests.get("https://v3.football.api-sports.io/odds", headers=headers, params={"fixture": fix_id}, verify=False, timeout=5)
                    d_odds = res_odds.json()
                    
                    if d_odds.get('response'):
                        apuestas = d_odds['response'][0]['bookmakers'][0]['bets']
                        for ap in apuestas:
                            if ap['name'] == 'Match Winner' or ap['id'] == 1:
                                for val in ap['values']:
                                    if str(val['value']).lower() == 'home': c_1 = val['odd']
                                    elif str(val['value']).lower() == 'draw': c_x = val['odd']
                                    elif str(val['value']).lower() == 'away': c_2 = val['odd']
                            elif ap['name'] == 'Goals Over/Under' or ap['id'] == 5:
                                for val in ap['values']:
                                    if val['value'] == 'Over 2.5': c_over25 = val['odd']
                            elif ap['name'] == 'Both Teams Score' or ap['id'] == 8:
                                for val in ap['values']:
                                    if str(val['value']).lower() == 'yes': c_btts = val['odd']
                except:
                    pass

                # FILTRO DE RENTABILIDAD: Solo picks con cuota >= 1.50
                pick_encontrado = False
                mercado_claro = ""
                pick_final = ""
                cuota_final = ""

                if val_h >= 50 and c_1 != "-" and float(c_1) >= 1.50:
                    mercado_claro = "MERCADO: Ganador Directo (Local)"
                    pick_final = f"Gana {p['teams']['home']['name']}"
                    cuota_final = c_1
                    pick_encontrado = True
                elif val_a >= 50 and c_2 != "-" and float(c_2) >= 1.50:
                    mercado_claro = "MERCADO: Ganador Directo (Visita)"
                    pick_final = f"Gana {p['teams']['away']['name']}"
                    cuota_final = c_2
                    pick_encontrado = True
                
                if not pick_encontrado:
                    if c_btts != "-" and float(c_btts) >= 1.50:
                        mercado_claro = "MERCADO: Ambos Equipos Anotan"
                        pick_final = "Ambos Marcan (SÍ)"
                        cuota_final = c_btts
                        pick_encontrado = True
                    elif c_over25 != "-" and float(c_over25) >= 1.50:
                        mercado_claro = "MERCADO: Total de Goles"
                        pick_final = "Más de 2.5 Goles (+2.5)"
                        cuota_final = c_over25
                        pick_encontrado = True

                # Si ninguna cuota supera el 1.50, saltamos este partido
                if not pick_encontrado:
                    continue

                datos_partido = {
                    "liga": p['league']['name'],
                    "hora": hora_sola,
                    "local": p['teams']['home']['name'],
                    "visita": p['teams']['away']['name'],
                    "mercado": mercado_claro,
                    "pick": pick_final,
                    "cuota_pick": cuota_final,
                    "prob_h": pred['percent']['home'],
                    "prob_d": pred['percent']['draw'],
                    "prob_a": pred['percent']['away'],
                    "c_1": c_1,
                    "c_x": c_x,
                    "c_2": c_2
                }
                
                resultados_ui.append(datos_partido)
            
            if resultados_ui:
                Clock.schedule_once(lambda dt, res=resultados_ui: self.mostrar_partidos(res))
            else:
                Clock.schedule_once(lambda dt: self.actualizar_estado("No hay cuotas rentables (+1.50) ahora mismo."))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.actualizar_estado("FALLA DE RED. Revisa tu conexion."))

    def mostrar_partidos(self, resultados):
        texto_msg = f"¡{len(resultados)} Pronosticos Rentables Cargados!"
        self.estado.text = texto_msg
        for datos in resultados:
            tarjeta = TarjetaPronostico(datos=datos)
            self.lista_partidos.add_widget(tarjeta)
            
        self.btn_cargar.disabled = False
        
    def actualizar_estado(self, texto):
        self.estado.text = texto
        self.btn_cargar.disabled = False

if __name__ == '__main__':
    TuPronosticosApp().run()
