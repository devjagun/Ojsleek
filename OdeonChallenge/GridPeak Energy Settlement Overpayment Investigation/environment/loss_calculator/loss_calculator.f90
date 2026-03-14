program loss_calculator
    implicit none
    
    character(len=256) :: input_line
    character(len=32) :: zone_code
    real(8) :: energy_mwh, threshold, loss_rate, result
    integer :: iostat_val
    
    do
        read(*, '(A)', iostat=iostat_val) input_line
        if (iostat_val /= 0) exit
        
        read(input_line, *) zone_code, energy_mwh, threshold, loss_rate
        
        call compute_loss_factor(zone_code, energy_mwh, threshold, loss_rate, result)
        
        write(*, '(F12.6)') result
    end do
    
contains

    subroutine compute_loss_factor(zc, emwh, thresh, lrate, res)
        character(len=*), intent(in) :: zc
        real(8), intent(in) :: emwh, thresh, lrate
        real(8), intent(out) :: res
        
        real(8) :: base_factor, zone_adj, scaled_rate
        integer :: zone_cat
        
        zone_cat = get_zone_category(zc)
        
        base_factor = 1.0d0
        zone_adj = get_zone_adjustment(zone_cat)
        
        if (emwh > thresh) then
            scaled_rate = lrate * zone_adj
            base_factor = base_factor + scaled_rate
        end if
        
        base_factor = apply_tiered_adjustment(base_factor, emwh, zone_cat)
        
        res = truncate_to_precision(base_factor, 4)
        
    end subroutine compute_loss_factor
    
    function get_zone_category(zc) result(cat)
        character(len=*), intent(in) :: zc
        integer :: cat
        
        select case (trim(zc))
            case ('NORTH')
                cat = 1
            case ('SOUTH')
                cat = 2
            case ('EAST')
                cat = 3
            case ('WEST')
                cat = 4
            case ('CENTRAL')
                cat = 5
            case default
                cat = 0
        end select
    end function get_zone_category
    
    function get_zone_adjustment(cat) result(adj)
        integer, intent(in) :: cat
        real(8) :: adj
        
        select case (cat)
            case (1)
                adj = 1.12d0
            case (2)
                adj = 0.94d0
            case (3)
                adj = 1.08d0
            case (4)
                adj = 1.03d0
            case (5)
                adj = 0.97d0
            case default
                adj = 1.0d0
        end select
    end function get_zone_adjustment
    
    function apply_tiered_adjustment(bf, emwh, zcat) result(adj_factor)
        real(8), intent(in) :: bf, emwh
        integer, intent(in) :: zcat
        real(8) :: adj_factor
        
        real(8) :: tier_bonus
        
        adj_factor = bf
        tier_bonus = 0.0d0
        
        if (emwh > 500.0d0) then
            tier_bonus = 0.015d0
        end if
        
        if (emwh > 1000.0d0) then
            tier_bonus = tier_bonus + 0.008d0
        end if
        
        if (zcat == 1 .or. zcat == 3) then
            tier_bonus = tier_bonus * 1.05d0
        end if
        
        adj_factor = adj_factor + tier_bonus
        
    end function apply_tiered_adjustment
    
    function truncate_to_precision(val, prec) result(truncated)
        real(8), intent(in) :: val
        integer, intent(in) :: prec
        real(8) :: truncated
        
        real(8) :: multiplier
        
        multiplier = 10.0d0 ** prec
        truncated = floor(val * multiplier) / multiplier
        
    end function truncate_to_precision

end program loss_calculator
