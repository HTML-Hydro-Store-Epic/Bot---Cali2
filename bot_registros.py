import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import datetime
from flask import Flask
from threading import Thread
import os

# === SERVIDOR WEB PARA MANTENER BOT ACTIVO ===
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot de Cali Roleplay está ONLINE! | Creado por Gost"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Iniciar servidor web
keep_alive()
# === FIN SERVIDOR WEB ===

# Configuración con todos los intents
intents = discord.Intents.all()

# Crear el bot con información personalizada en el perfil
bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    description="🤖 Bot oficial de Cali Roleplay\n📋 Sistema de registros staff\n✨ Creado por Gost"
)

# Configurar base de datos
def init_db():
    conn = sqlite3.connect('registros.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            rango TEXT NOT NULL,
            hora_entrada TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Función para obtener el rango más alto (con más permisos)
def obtener_rango_mas_alto(member):
    try:
        # Ordenar roles por posición (más alta primero = más permisos)
        roles_ordenados = sorted(member.roles, key=lambda role: role.position, reverse=True)
        
        # Excluir @everyone y obtener el rol más alto
        for role in roles_ordenados:
            if role.name != "@everyone" and role.name:
                return role.name
        return "Miembro"
    except Exception as e:
        print(f"Error obteniendo rango: {e}")
        return "Miembro"

@bot.event
async def on_ready():
    print('=' * 60)
    print('🤖 BOT PERSONALIZADO PARA CALI ROLEPLAY')
    print('📋 SISTEMA DE REGISTROS STAFF')
    print('✨ CREADOR: GHOST')
    print('=' * 60)
    print(f'🎉 Bot conectado como: {bot.user.name}')
    print(f'🆔 ID del bot: {bot.user.id}')
    print(f'📡 Conectado a: {len(bot.guilds)} servidor(es)')
    print('=' * 60)
    
    # Establecer estado personalizado que se ve en el perfil
    actividad = discord.Activity(
        type=discord.ActivityType.watching,
        name="Cali Roleplay | /duty"
    )
    await bot.change_presence(
        activity=actividad,
        status=discord.Status.online
    )
    
    # Cambiar el "acerca de" del bot (se ve en el perfil)
    try:
        # Esto cambia la descripción pública del bot
        await bot.application.edit(
            description="🤖 **Bot Oficial de Cali Roleplay**\n\n📋 **Sistema de Registros Staff**\n⚙️ Control de horarios y presencia\n✨ **Creado por: Gost**",
        )
        print("✅ Perfil del bot actualizado correctamente")
    except Exception as e:
        print(f"⚠️ No se pudo actualizar el perfil del bot: {e}")
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ Comandos sincronizados: {len(synced)}')
        for cmd in synced:
            print(f'   - /{cmd.name}')
    except Exception as e:
        print(f'❌ Error sincronizando comandos: {e}')
    
    print('🚀 Sistema de registros staff listo!')
    print('=' * 60)

@bot.tree.command(name="duty", description="🎯 Encender registro - Iniciar servicio staff")
async def duty(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        c.execute("SELECT * FROM registros WHERE user_id = ?", (user_id,))
        
        if c.fetchone():
            embed = discord.Embed(
                title="❌ **REGISTRO DENEGADO**",
                description="Ya tienes un registro activo en el sistema.\n\nUsa `/offduty` para apagar tu registro actual.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            conn.close()
            return
        
        # Obtener información del usuario
        nombre_usuario = interaction.user.display_name
        rango = obtener_rango_mas_alto(interaction.user)
        hora_entrada = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        # Insertar en la base de datos
        c.execute(
            "INSERT INTO registros (user_id, username, rango, hora_entrada) VALUES (?, ?, ?, ?)",
            (user_id, str(interaction.user), rango, hora_entrada)
        )
        conn.commit()
        conn.close()
        
        # Crear embed con el formato solicitado
        embed = discord.Embed(
            title="📋 **REGISTRO STAFF - ENCENDIDO**",
            description="Servicio staff iniciado correctamente",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="*️⃣ **Nombre**", value=f"```{nombre_usuario}```", inline=False)
        embed.add_field(name="🎭 **Rol**", value=f"```{rango}```", inline=False)
        embed.add_field(name="🕐 **Hora de Entrada**", value=f"```{hora_entrada}```", inline=False)
        embed.add_field(name="📝 **Estado**", value="```🟢 EN SERVICIO```", inline=False)
        
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed.set_footer(text="🤖 Cali Roleplay • Creado por Gost")
        
        await interaction.response.send_message(embed=embed)
        
        print(f"📝 Registro encendido: {nombre_usuario} - Rol: {rango}")
        
    except Exception as e:
        print(f"❌ Error en duty: {e}")
        await interaction.response.send_message("❌ Ocurrió un error al encender el registro.", ephemeral=True)

@bot.tree.command(name="miregistro", description="📊 Ver mi información de registro staff")
async def miregistro(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        c.execute("SELECT * FROM registros WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        conn.close()
        
        if not user_data:
            embed = discord.Embed(
                title="❌ **SIN REGISTRO ACTIVO**",
                description="No tienes un registro activo en el sistema staff.\n\nUsa `/duty` para iniciar servicio.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # user_data: (id, user_id, username, rango, hora_entrada, fecha_registro)
        nombre_usuario = interaction.user.display_name
        
        embed = discord.Embed(
            title="📋 **TU REGISTRO STAFF**",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="*️⃣ **Nombre**", value=f"```{nombre_usuario}```", inline=False)
        embed.add_field(name="🎭 **Rol**", value=f"```{user_data[3]}```", inline=False)
        embed.add_field(name="🕐 **Hora de Entrada**", value=f"```{user_data[4]}```", inline=False)
        embed.add_field(name="📅 **Fecha de Registro**", value=f"```{user_data[5]}```", inline=False)
        embed.add_field(name="📝 **Estado**", value="```🟢 EN SERVICIO```", inline=False)
        
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed.set_footer(text="🤖 Cali Roleplay • Creado por Gost")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        print(f"❌ Error viendo registro: {e}")
        await interaction.response.send_message("❌ Ocurrió un error al obtener tu registro.", ephemeral=True)

@bot.tree.command(name="offduty", description="🔴 Apagar registro - Finalizar servicio staff")
async def offduty(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        
        # Conectar a la base de datos
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        
        # Buscar registro del usuario
        c.execute("SELECT * FROM registros WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        
        if not user_data:
            embed = discord.Embed(
                title="❌ **SIN REGISTRO ACTIVO**",
                description="No tienes un registro activo para apagar.\n\nUsa `/duty` para iniciar servicio primero.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            conn.close()
            return
        
        # Guardar información antes de eliminar
        rango_anterior = user_data[3]
        hora_entrada = user_data[4]
        hora_salida = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        nombre_usuario = interaction.user.display_name
        
        # Calcular tiempo de servicio
        entrada_dt = datetime.datetime.strptime(hora_entrada, "%H:%M:%S %d/%m/%Y")
        salida_dt = datetime.datetime.now()
        tiempo_servicio = salida_dt - entrada_dt
        horas = int(tiempo_servicio.total_seconds() // 3600)
        minutos = int((tiempo_servicio.total_seconds() % 3600) // 60)
        
        # Eliminar el registro
        c.execute("DELETE FROM registros WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # Crear embed de confirmación
        embed = discord.Embed(
            title="🔴 **SERVICIO FINALIZADO**",
            description="Tu registro staff ha sido apagado correctamente.",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="👤 **Usuario**", value=f"```{nombre_usuario}```", inline=False)
        embed.add_field(name="🎭 **Rol**", value=f"```{rango_anterior}```", inline=False)
        embed.add_field(name="🕐 **Hora de Entrada**", value=f"```{hora_entrada}```", inline=False)
        embed.add_field(name="🕒 **Hora de Salida**", value=f"```{hora_salida}```", inline=False)
        embed.add_field(name="⏱️ **Tiempo de Servicio**", value=f"```{horas}h {minutos}m```", inline=False)
        embed.add_field(name="📝 **Estado**", value="```🔴 FUERA DE SERVICIO```", inline=False)
        
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed.set_footer(text="🤖 Cali Roleplay • Creado por Gost")
        
        await interaction.response.send_message(embed=embed)
        
        print(f"🔴 Registro apagado: {nombre_usuario} - Tiempo: {horas}h {minutos}m")
        
    except Exception as e:
        print(f"❌ Error en offduty: {e}")
        await interaction.response.send_message("❌ Ocurrió un error al apagar el registro.", ephemeral=True)

@bot.tree.command(name="estadisticas", description="📈 Ver estadísticas del sistema staff")
async def estadisticas(interaction: discord.Interaction):
    try:
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        
        # Total de registros
        c.execute("SELECT COUNT(*) FROM registros")
        total_registros = c.fetchone()[0]
        
        # Registro más reciente
        c.execute("SELECT username, rango, hora_entrada FROM registros ORDER BY fecha_registro DESC LIMIT 1")
        ultimo_registro = c.fetchone()
        
        conn.close()
        
        embed = discord.Embed(
            title="📊 **ESTADÍSTICAS STAFF**",
            description="Estadísticas en tiempo real del sistema",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="👥 **Staff Activo**", value=f"```{total_registros}```", inline=True)
        
        if ultimo_registro:
            # Extraer solo el nombre del usuario (sin el #1234)
            nombre_usuario = ultimo_registro[0].split('#')[0]
            embed.add_field(name="🆕 **Último en Servicio**", value=f"```{nombre_usuario}```", inline=True)
            embed.add_field(name="🎭 **Rol**", value=f"```{ultimo_registro[1]}```", inline=True)
            embed.add_field(name="🕐 **Hora de Entrada**", value=f"```{ultimo_registro[2]}```", inline=True)
        
        embed.set_footer(text="🤖 Cali Roleplay • Creado por Gost")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
        await interaction.response.send_message("❌ Ocurrió un error al obtener las estadísticas.", ephemeral=True)

@bot.tree.command(name="staff", description="👨‍💼 Ver todos los staff en servicio (Solo administradores)")
async def staff(interaction: discord.Interaction):
    try:
        # Verificar permisos de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ No tienes permisos para ver todos los registros staff.", ephemeral=True)
            return
        
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        c.execute("SELECT username, rango, hora_entrada, fecha_registro FROM registros ORDER BY fecha_registro DESC")
        registros = c.fetchall()
        conn.close()
        
        if not registros:
            embed = discord.Embed(
                title="📋 **STAFF EN SERVICIO**",
                description="No hay staff activo en este momento.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Crear embed con los registros
        embed = discord.Embed(
            title="📋 **STAFF EN SERVICIO**",
            description=f"**Total de staff activo:** ```{len(registros)}```",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        for i, registro in enumerate(registros[:15], 1):  # Mostrar primeros 15
            # Extraer solo el nombre del usuario (sin el #1234)
            nombre_usuario = registro[0].split('#')[0]
            embed.add_field(
                name=f"**{i}. {nombre_usuario}**",
                value=f"🎭 **Rol:** {registro[1]}\n🕐 **Entrada:** {registro[2]}\n📅 **Desde:** {registro[3]}",
                inline=False
            )
        
        if len(registros) > 15:
            embed.set_footer(text=f"🤖 Cali Roleplay • Mostrando 15 de {len(registros)} staff activo")
        else:
            embed.set_footer(text="🤖 Cali Roleplay • Creado por Gost")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"❌ Error viendo staff: {e}")
        await interaction.response.send_message("❌ Ocurrió un error al obtener el staff activo.", ephemeral=True)

@bot.tree.command(name="info", description="ℹ️ Información del bot y créditos")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 **INFORMACIÓN DEL BOT**",
        description="Sistema de Registros Staff para Cali Roleplay",
        color=discord.Color.purple(),
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name="🎯 **Propósito**", value="Sistema de registro y control para el staff del servidor", inline=False)
    embed.add_field(name="⚙️ **Funcionalidades**", value="• Registro de staff activo\n• Control de horarios\n• Estadísticas en tiempo real\n• Gestión de roles", inline=False)
    embed.add_field(name="👨‍💻 **Desarrollador**", value="```Gost```", inline=True)
    embed.add_field(name="🏢 **Para**", value="```Cali Roleplay```", inline=True)
    embed.add_field(name="📅 **Versión**", value="```1.0```", inline=True)
    
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url)
    embed.set_footer(text="🤖 Cali Roleplay • Sistema de Registros Staff")
    
    await interaction.response.send_message(embed=embed)

# Comando para forzar sincronización
@bot.command()
async def sync(ctx):
    if ctx.author.guild_permissions.administrator:
        try:
            synced = await bot.tree.sync()
            await ctx.send(f'✅ Comandos sincronizados: {len(synced)}')
        except Exception as e:
            await ctx.send(f'❌ Error: {e}')
    else:
        await ctx.send('❌ No tienes permisos')

# TU TOKEN desde variable de entorno
TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    init_db()
    print('=' * 60)
    print('🚀 INICIANDO BOT PERSONALIZADO CALI ROLEPLAY')
    print('✨ CREADOR: GHOST')
    print('=' * 60)
    
    if not TOKEN:
        print("❌ ERROR: No se encontró DISCORD_TOKEN")
        print("💡 Configura la variable en Render.com")
    else:
        bot.run(TOKEN)
