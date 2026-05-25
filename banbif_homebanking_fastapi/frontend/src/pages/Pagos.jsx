import { useEffect, useMemo, useState } from "react";
import { SUPABASE_URL, SUPABASE_KEY } from "../supabaseDirectConfig";

function money(value) {
  return `S/ ${Number(value || 0).toFixed(2)}`;
}

function headers(extra = {}) {
  return {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
    ...extra,
  };
}

async function supabaseRequest(url, options = {}) {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    throw new Error("No se cargaron las credenciales de Supabase.");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    const text = await res.text();
    const result = text ? JSON.parse(text) : null;

    if (!res.ok) {
      throw new Error(
        result?.message ||
        result?.hint ||
        result?.details ||
        `Error HTTP ${res.status}`
      );
    }

    return result;
  } finally {
    clearTimeout(timer);
  }
}

export default function Pagos({ user, data, reload, showToast }) {
  const cuentas = data?.accounts || [];

  const [pagos, setPagos] = useState([]);
  const [accountId, setAccountId] = useState(cuentas?.[0]?.id || "");
  const [servicio, setServicio] = useState("luz");
  const [numeroContrato, setNumeroContrato] = useState("");
  const [monto, setMonto] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [tipoMensaje, setTipoMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  const userId = user?.id || data?.user?.id || 1;

  useEffect(() => {
    if (!accountId && cuentas?.[0]?.id) {
      setAccountId(cuentas[0].id);
    }
  }, [cuentas, accountId]);

  const selectedAccount = useMemo(() => {
    return cuentas.find((a) => String(a.id) === String(accountId)) || cuentas[0];
  }, [cuentas, accountId]);

  async function cargarPagos() {
    try {
      const url =
        `${SUPABASE_URL}/rest/v1/pagos` +
        `?select=*&user_id=eq.${Number(userId)}&order=created_at.desc`;

      const result = await supabaseRequest(url, {
        method: "GET",
        headers: headers(),
      });

      setPagos(Array.isArray(result) ? result : []);
    } catch (error) {
      console.error("Error cargando pagos:", error);
      setMensaje("No se pudo cargar pagos: " + error.message);
      setTipoMensaje("error");
    }
  }

  useEffect(() => {
    cargarPagos();
  }, [userId]);

  async function registrarPago(e) {
    e.preventDefault();

    setMensaje("");
    setTipoMensaje("");

    const montoNumero = Number(monto);

    if (!selectedAccount) {
      setMensaje("No hay una cuenta disponible para realizar el pago.");
      setTipoMensaje("error");
      return;
    }

    if (!numeroContrato.trim() || !montoNumero || montoNumero <= 0) {
      setMensaje("Completa el numero de contrato y un monto valido.");
      setTipoMensaje("error");
      return;
    }

    setCargando(true);

    try {
      const nuevoPago = {
        user_id: Number(userId),
        account_id: Number(selectedAccount.id),
        servicio,
        numero_contrato: numeroContrato.trim(),
        monto: montoNumero,
        estado: "completado",
      };

      const result = await supabaseRequest(`${SUPABASE_URL}/rest/v1/pagos`, {
        method: "POST",
        headers: headers({
          Prefer: "return=representation",
        }),
        body: JSON.stringify([nuevoPago]),
      });

      console.log("Pago registrado:", result);

      setMensaje("Pago registrado correctamente.");
      setTipoMensaje("success");

      if (showToast) showToast("Pago registrado correctamente");

      setNumeroContrato("");
      setMonto("");

      await cargarPagos();
      if (reload) await reload();
    } catch (error) {
      console.error("Error registrando pago:", error);
      setMensaje("No se pudo registrar el pago: " + error.message);
      setTipoMensaje("error");
    } finally {
      setCargando(false);
    }
  }

  return (
    <main className="pagos-page">
      <section className="pagos-card pagos-hero">
        <span className="pagos-tag">PAGOS</span>
        <h1>Pagos de servicios</h1>
        <p>
          Realiza pagos de luz, agua, telefono, internet o gas desde tu banca digital.
        </p>
      </section>

      <section className="pagos-card">
        <h2>Nuevo pago</h2>

        <form className="pagos-form" onSubmit={registrarPago}>
          <label>
            Cuenta de origen
            <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
              {cuentas.length === 0 ? (
                <option value="">No tienes cuentas registradas</option>
              ) : (
                cuentas.map((cuenta) => (
                  <option key={cuenta.id} value={cuenta.id}>
                    {cuenta.account_number} - {cuenta.account_type} - {cuenta.currency || "PEN"}{" "}
                    {Number(cuenta.balance || 0).toFixed(2)}
                  </option>
                ))
              )}
            </select>
          </label>

          <label>
            Servicio
            <select value={servicio} onChange={(e) => setServicio(e.target.value)}>
              <option value="luz">Luz</option>
              <option value="agua">Agua</option>
              <option value="telefono">Telefono</option>
              <option value="internet">Internet</option>
              <option value="gas">Gas</option>
            </select>
          </label>

          <label>
            Numero de contrato
            <input
              type="text"
              value={numeroContrato}
              onChange={(e) => setNumeroContrato(e.target.value)}
              placeholder="Ej: CTR-001"
            />
          </label>

          <label>
            Monto a pagar
            <input
              type="number"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="Ej: 85.50"
              min="1"
              step="0.01"
            />
          </label>

          <button type="submit" disabled={cargando || cuentas.length === 0}>
            {cargando ? "Procesando..." : "Pagar servicio"}
          </button>

          {mensaje && (
            <p className={`pagos-mensaje ${tipoMensaje === "error" ? "pagos-error" : ""}`}>
              {mensaje}
            </p>
          )}
        </form>
      </section>

      <section className="pagos-card">
        <h2>Historial de pagos</h2>

        {pagos.length === 0 ? (
          <p className="pagos-vacio">Aun no hay pagos registrados.</p>
        ) : (
          <div className="pagos-lista">
            {pagos.map((pago) => (
              <article className="pago-item" key={pago.id}>
                <div>
                  <strong>{String(pago.servicio).toUpperCase()}</strong>
                  <p>Contrato: {pago.numero_contrato}</p>
                </div>

                <div className="pago-monto">
                  <strong>{money(pago.monto)}</strong>
                  <p>{pago.estado}</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
