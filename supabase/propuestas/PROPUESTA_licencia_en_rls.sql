-- PROPUESTA — NO APLICADA. Revisar y aprobar antes de ejecutar en Supabase.
--
-- Problema 1: las políticas de app_records solo exigen auth.uid() = user_id.
-- La licencia se valida únicamente en el navegador, así que cualquier cuenta
-- registrada (el alta está abierta) puede leer y escribir sus propios registros
-- llamando a la API directamente, sin licencia activa.
--
-- Problema 2: activate_device_license reactiva un dispositivo revocado
-- (on conflict ... set revoked_at = null). Revocar un equipo no lo bloquea:
-- basta con volver a abrir la app en ese equipo si queda cupo.
--
-- Probar primero en un proyecto o rama de pruebas.

-- 1) Función auxiliar: ¿la cuenta tiene al menos un dispositivo activo con licencia vigente?
create or replace function public.has_active_license()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.license_devices d
    join public.licenses l on l.id = d.license_id
    where d.user_id = auth.uid()
      and d.revoked_at is null
      and l.status in ('active','grace_period')
      and l.starts_at <= now()
      and (l.expires_at is null or l.expires_at > now())
  );
$$;
revoke all on function public.has_active_license() from public;
grant execute on function public.has_active_license() to authenticated;

-- 2) Políticas de app_records que además exigen licencia vigente.
drop policy if exists "users read own records" on public.app_records;
create policy "users read own records" on public.app_records for select
  to authenticated using (auth.uid() = user_id and public.has_active_license());

drop policy if exists "users insert own records" on public.app_records;
create policy "users insert own records" on public.app_records for insert
  to authenticated with check (auth.uid() = user_id and public.has_active_license());

drop policy if exists "users update own records" on public.app_records;
create policy "users update own records" on public.app_records for update
  to authenticated using (auth.uid() = user_id and public.has_active_license())
  with check (auth.uid() = user_id and public.has_active_license());

drop policy if exists "users delete own records" on public.app_records;
create policy "users delete own records" on public.app_records for delete
  to authenticated using (auth.uid() = user_id and public.has_active_license());

-- 3) En activate_device_license, no reactivar un dispositivo revocado por el administrador.
--    Sustituir el bloque final de inserción por:
--
--  if exists (select 1 from public.license_devices
--             where license_id = v_lic.id and user_id = v_uid and device_id = p_device_id
--               and revoked_at is not null) then
--    return jsonb_build_object('ok',false,'message','Este dispositivo fue dado de baja. Contacte al administrador.');
--  end if;
--  insert into public.license_devices(license_id,user_id,device_id,device_type,last_seen_at,revoked_at)
--  values (v_lic.id,v_uid,p_device_id,p_device_type,now(),null)
--  on conflict (license_id,user_id,device_id) do update set last_seen_at = now();
--
-- Nota: con (3), para liberar un cupo el administrador debe borrar la fila del
-- dispositivo en vez de marcar revoked_at, o se debe acordar otra convención.
