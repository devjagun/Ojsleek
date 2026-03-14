program bc
    implicit none
    
    integer :: d, n, t, zd, ty
    real(8) :: bd, ar, s
    character(10) :: tr
    real(8) :: p, z, r, f
    character(256) :: l
    integer :: e
    
    read(*,'(A)',iostat=e) l
    if (e /= 0) stop 1
    
    read(l,*) d, n, t, bd, ar, zd, tr, ty
    
    p = cb(n, t)
    z = cz(bd, ar, zd)
    s = p * z
    r = gr(tr, s, ty)
    f = s * r
    
    write(*,'(I8,F12.2,F12.3,F12.2,F8.4,F12.2)') d, p, z, s, r, f
    
contains

    function cb(n, t) result(v)
        integer, intent(in) :: n, t
        real(8) :: v
        real(8) :: x, a
        
        x = real(n - t, 8)
        
        if (x > 0.0d0) then
            a = x * 1.15d0
        else
            a = x * 0.85d0
        end if
        
        v = real(t, 8) + a
        v = dnint(v * 100.0d0) / 100.0d0
        
    end function cb
    
    function cz(bd, ar, zd) result(v)
        real(8), intent(in) :: bd, ar
        integer, intent(in) :: zd
        real(8) :: v
        real(8) :: rf, ff
        
        if (ar > 4.2d0) then
            rf = 0.92d0
        else
            rf = 1.0d0
        end if
        
        if (zd >= 30) then
            ff = 0.88d0
        else
            ff = 1.0d0
        end if
        
        v = bd * rf * ff
        v = dnint(v * 1000.0d0) / 1000.0d0
        
    end function cz
    
    function gr(tr, s, ty) result(v)
        character(*), intent(in) :: tr
        real(8), intent(in) :: s
        integer, intent(in) :: ty
        real(8) :: v
        
        if (trim(tr) == 'Gold') then
            v = 1.15d0
        else if (s > 150.0d0) then
            v = 1.10d0
        else if (trim(tr) == 'Gold' .and. s > 150.0d0) then
            v = 1.25d0
        else if (ty > 2) then
            v = 1.05d0
        else
            v = 1.00d0
        end if
        
    end function gr

end program bc
