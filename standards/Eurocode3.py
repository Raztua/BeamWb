import math
import numpy as np
from standards.BaseStandard import BaseStandard
from standards.Registry import StandardsRegistry

# Try to import PrettyTable for nice reporting
try:
    from prettytable import PrettyTable

    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False


class Eurocode3Standard(BaseStandard):
    name = "Eurocode 3 (EN 1993-1-1)"

    def __init__(self, beam_obj, section_props, mat_props, forces):
        super().__init__(beam_obj, section_props, mat_props, forces)

        # [NEW] Capture the explicit section type passed from CodeCheck
        self.section_type = self.sec.get('type', 'Unknown')

        # --- 1. Geometric Properties (Safely Loaded) ---
        self.h = self.sec.get('h', 0.0)
        self.b = self.sec.get('b', 0.0)
        self.tw = self.sec.get('tw', 0.0)
        self.tf = self.sec.get('tf', 0.0)
        self.d = self.sec.get('d', 0.0)  # Diameter for pipes
        self.t = self.sec.get('t', 0.0)  # Thickness for pipes/boxes
        self.L = self.sec.get('L', 1.0)

        # Primary Structural Properties
        self.A = self.sec.get('A', 0.0)
        self.Iy = self.sec.get('Iy', 0.0)
        self.Iz = self.sec.get('Iz', 0.0)

        # Radii of Gyration
        self.iy = math.sqrt(self.Iy / self.A) if self.A > 0 else 0
        self.iz = math.sqrt(self.Iz / self.A) if self.A > 0 else 0

        # --- 2. Torsion & Warping ---
        if 'J' in self.sec and self.sec['J'] > 0:
            self.It = self.sec['J']
        else:
            if self.d > 0:  # Tubular
                self.It = (math.pi * (self.d ** 4 - (self.d - 2 * self.t) ** 4)) / 32
            elif self.tw > 0 and self.tf > 0:  # Open Section
                self.It = (1 / 3) * (2 * self.b * self.tf ** 3 + (self.h - 2 * self.tf) * self.tw ** 3)
            else:
                self.It = self.Iy * 0.01

        # Warping Constant (Iw)
        if self.tw > 0 and self.tf > 0 and self.d == 0:
            hs = self.h - self.tf
            self.Iw = (self.Iz * hs ** 2) / 4
        else:
            self.Iw = 0.0

        # --- 3. Moduli (Elastic & Plastic) ---
        self.Wel_y = self.sec.get('Wel_y', self.Iy / (self.h / 2) if self.h > 0 else 0)
        self.Wel_z = self.sec.get('Wel_z', self.Iz / (self.b / 2) if self.b > 0 else 0)

        sf = 1.25 if (self.d > 0 or (self.b > 0 and self.tw == self.tf)) else 1.14
        self.Wpl_y = self.sec.get('Wpl_y', self.Wel_y * sf)
        self.Wpl_z = self.sec.get('Wpl_z', self.Wel_z * sf)

        # --- 4. Material ---
        self.fy = self.mat.get('fy', 235e6)
        self.E = self.mat.get('E', 210e9)
        self.G = self.mat.get('G', 81e9)
        self.epsilon = math.sqrt(235e6 / self.fy)

    @classmethod
    def get_parameter_definitions(cls):
        return {
            "GammaM0": ("App::PropertyFloat", 1.0, "Partial factor for cross-section resistance"),
            "GammaM1": ("App::PropertyFloat", 1.0, "Partial factor for instability"),
            "Lcr_y_ratio": ("App::PropertyFloat", 1.0, "Buckling length factor y-y (Strong axis)"),
            "Lcr_z_ratio": ("App::PropertyFloat", 1.0, "Buckling length factor z-z (Weak axis)"),
            "LTB_curve": ("App::PropertyEnumeration", "a", "LTB Buckling Curve", ["a", "b", "c", "d"]),
            "Buckling_curve_y": ("App::PropertyEnumeration", "a", "Flexural Buckling Curve y-y", ["a", "b", "c", "d"]),
            "Buckling_curve_z": ("App::PropertyEnumeration", "b", "Flexural Buckling Curve z-z", ["a", "b", "c", "d"]),
        }

    def run_check(self):
        gamma_m0 = self.parameters.get("GammaM0", 1.0)
        gamma_m1 = self.parameters.get("GammaM1", 1.0)
        ky = self.parameters.get("Lcr_y_ratio", 1.0)
        kz = self.parameters.get("Lcr_z_ratio", 1.0)

        Lcr_y = self.L * ky
        Lcr_z = self.L * kz

        # 1. Determine Class
        section_class = self._classify_section_geometry()
        st = self.section_type

        # 2. Shear Areas (Av) and Plastic Shear Resistance
        Av_y, Av_z = 0.0, 0.0

        # Logic based on Explicit Section Type
        if st == "Tubular":
            Av_y = (2 * self.A) / math.pi
            Av_z = (2 * self.A) / math.pi
        elif st in ["Rectangle", "HSS"]:
            Av_z = (self.A * self.h) / (self.h + self.b)
            Av_y = (self.A * self.b) / (self.h + self.b)
        elif st in ["C-Shape", "U-Shape"]:
            Av_z = self.h * self.tw
            Av_y = 2 * self.b * self.tf
        elif st == "L-Shape":
            Av_z = self.h * self.tw
            Av_y = self.b * self.tf
        else:
            Av_z = self.A - 2 * self.b * self.tf + (self.tw + 2 * self.tf) * self.tw
            if Av_z < self.h * self.tw: Av_z = self.h * self.tw
            Av_y = 2 * self.b * self.tf

        Vpl_Rd_z = (Av_z * (self.fy / math.sqrt(3))) / gamma_m0
        Vpl_Rd_y = (Av_y * (self.fy / math.sqrt(3))) / gamma_m0

        # 3. Resistances (Moment & Axial)
        W_y_const = self.Wpl_y if section_class <= 2 else self.Wel_y
        W_z_const = self.Wpl_z if section_class <= 2 else self.Wel_z

        Mc_Rd_y = (W_y_const * self.fy) / gamma_m0
        Mc_Rd_z = (W_z_const * self.fy) / gamma_m0
        Nc_Rd = (self.A * self.fy) / gamma_m0

        # 4. Torsion Resistance (T_Rd)
        tau_Rd = self.fy / (math.sqrt(3) * gamma_m0)
        T_Rd = 1e-9  # Avoid div by zero

        if st in ["Tubular", "Rectangle", "HSS"]:
            if st == "Tubular":
                t_val = self.t
                d_mid = self.d - t_val
                Am = math.pi * (d_mid ** 2) / 4.0
            else:
                t_val = self.t if self.t > 0 else self.tw
                Am = (self.h - t_val) * (self.b - t_val)

            if t_val > 0: T_Rd = tau_Rd * 2 * Am * t_val
        else:
            if self.b > 0 and self.tw == self.tf:
                t_max = self.tw
            else:
                t_max = max(self.tf, self.tw)

            if t_max > 0: T_Rd = (tau_Rd * self.It) / t_max

        # 5. Stability (Buckling)
        Ncr_y = (math.pi ** 2 * self.E * self.Iy) / (Lcr_y ** 2)
        Ncr_z = (math.pi ** 2 * self.E * self.Iz) / (Lcr_z ** 2)

        lambda_y = math.sqrt(self.A * self.fy / Ncr_y) if Ncr_y > 0 else 0
        lambda_z = math.sqrt(self.A * self.fy / Ncr_z) if Ncr_z > 0 else 0

        chi_y = self._get_chi(lambda_y, self.parameters.get("Buckling_curve_y", "a"))
        chi_z = self._get_chi(lambda_z, self.parameters.get("Buckling_curve_z", "b"))

        Nb_Rd_y = (chi_y * self.A * self.fy) / gamma_m1
        Nb_Rd_z = (chi_z * self.A * self.fy) / gamma_m1

        # 6. Stability (LTB)
        L_LTB = Lcr_z
        term1 = (math.pi ** 2 * self.E * self.Iz) / (L_LTB ** 2)
        term2 = (self.Iw / self.Iz) + ((L_LTB ** 2 * self.G * self.It) / (math.pi ** 2 * self.E * self.Iz))
        Mcr = term1 * math.sqrt(term2)

        lambda_LT = math.sqrt((W_y_const * self.fy) / Mcr) if Mcr > 0 else 0
        chi_LT = self._get_chi_LT(lambda_LT, self.parameters.get("LTB_curve", "a"))
        Mb_Rd = (chi_LT * W_y_const * self.fy) / gamma_m1

        # --- 3. VECTORIZED ANALYSIS (Numpy) ---
        # Helper to ensure we have numpy arrays
        def to_arr(key):
            val = self.forces.get(key)
            if val is None or len(val) == 0:
                return np.zeros(1)
            return np.array(val)

        # Extract forces arrays (PyNite inputs usually: Tension (+), Compression (-))
        Ned = to_arr('P')
        My = np.abs(to_arr('My'))
        Mz = np.abs(to_arr('Mz'))
        Vy = np.abs(to_arr('Vy'))
        Vz = np.abs(to_arr('Vz'))
        Tx = np.abs(to_arr('Tx'))
        Pos = to_arr('x')

        # Identify Compression
        # EC3 uses Compression as positive N_Ed for stability checks usually
        Ned_comp = np.where(Ned < 0, np.abs(Ned), 0.0)

        # A. Cross Section Resistance Checks
        # Shear
        UC_shear_y = Vy / Vpl_Rd_y if Vpl_Rd_y > 0 else np.zeros_like(Vy)
        UC_shear_z = Vz / Vpl_Rd_z if Vpl_Rd_z > 0 else np.zeros_like(Vz)
        UC_torsion = Tx / T_Rd
        UC_shear = np.maximum(UC_shear_y, np.maximum(UC_shear_z, UC_torsion))

        # Combined Axial + Bending (Cross Section)
        UC_axial = Ned_comp / Nc_Rd
        UC_bend_y = My / Mc_Rd_y
        UC_bend_z = Mz / Mc_Rd_z
        UC_sec_combined = UC_axial + UC_bend_y + UC_bend_z

        # B. Stability Interaction (Method 2 - EN 1993-1-1 Annex B)
        # Interaction factors kyy, kzz, kyz, kzy

        # kyy
        denom_kyy = (chi_y * self.A * self.fy / gamma_m1)
        ny = Ned_comp / denom_kyy
        # Cmy assumed 0.9
        Cmy = 0.9
        kyy = Cmy * (1 + (lambda_y - 0.2) * ny)
        kyy = np.minimum(kyy, Cmy * (1 + 0.8 * ny))

        # kzz
        denom_kzz = (chi_z * self.A * self.fy / gamma_m1)
        nz = Ned_comp / denom_kzz
        Cmz = 0.9
        kzz = Cmz * (1 + (lambda_z - 0.2) * nz)
        kzz = np.minimum(kzz, Cmz * (1 + 0.8 * nz))

        # Cross terms
        kyz = 0.6 * kzz
        kzy = 0.6 * kyy

        # Eq 6.61 and 6.62
        denom_N_y = Nb_Rd_y
        denom_N_z = Nb_Rd_z
        denom_M_y = Mb_Rd  # LTB controls Major axis
        denom_M_z = Mc_Rd_z

        def safe_div(num, den):
            return np.divide(num, den, out=np.zeros_like(num), where=den != 0)

        term_N_y = safe_div(Ned_comp, denom_N_y)
        term_N_z = safe_div(Ned_comp, denom_N_z)
        term_M_y = safe_div(My, denom_M_y)
        term_M_z = safe_div(Mz, denom_M_z)

        uc_stab_661 = term_N_y + kyy * term_M_y + kyz * term_M_z
        uc_stab_662 = term_N_z + kzy * term_M_y + kzz * term_M_z

        uc_stability = np.maximum(uc_stab_661, uc_stab_662)

        # C. Total Unity Check
        TOTAL_UC = np.maximum(UC_sec_combined, np.maximum(uc_stability, UC_shear))

        # --- 4. Result Packaging ---
        max_val = float(np.max(TOTAL_UC))
        crit_idx = np.argmax(TOTAL_UC)

        # Create critical data dictionary for logging (Scalars)
        crit_data = {
            'pos': float(Pos[crit_idx]),
            'Ned': float(Ned[crit_idx]),
            'My': float(My[crit_idx]),
            'Mz': float(Mz[crit_idx]),
            'Vy': float(Vy[crit_idx]),
            'Vz': float(Vz[crit_idx]),
            'Tx': float(Tx[crit_idx]),

            'Nc_Rd': Nc_Rd, 'Mc_Rd_y': Mc_Rd_y, 'Mc_Rd_z': Mc_Rd_z,
            'Vpl_Rd_y': Vpl_Rd_y, 'Vpl_Rd_z': Vpl_Rd_z, 'T_Rd': T_Rd,
            'Nb_Rd_y': Nb_Rd_y, 'Nb_Rd_z': Nb_Rd_z, 'Mb_Rd': Mb_Rd,

            'uc_sec': float(UC_sec_combined[crit_idx]),
            'uc_stab': float(uc_stability[crit_idx]),
            'uc_shear': float(UC_shear[crit_idx]),
            'uc_stab_661': float(uc_stab_661[crit_idx]),
            'uc_stab_662': float(uc_stab_662[crit_idx]),
            'uc_torsion': float(UC_torsion[crit_idx]),

            'lambda_y': lambda_y, 'lambda_z': lambda_z, 'lambda_LT': lambda_LT,
            'chi_y': chi_y, 'chi_z': chi_z, 'chi_LT': chi_LT,
            'kyy': float(kyy[crit_idx]), 'kzz': float(kzz[crit_idx]),
            'kyz': float(kyz[crit_idx]), 'kzy': float(kzy[crit_idx]),
            'Ncr_y': Ncr_y, 'Ncr_z': Ncr_z, 'Mcr': Mcr,
            'W_y': W_y_const, 'W_z': W_z_const
        }

        log_str = self._generate_log(section_class, Lcr_y, Lcr_z, crit_data, max_val)

        return {
            'values': TOTAL_UC.tolist(),
            'max_uc': max_val,
            'detailed_log': log_str
        }

    def _generate_log(self, s_class, Lcr_y, Lcr_z, c, max_uc):
        """Generate verbose calculation log"""
        lines = []
        lines.append("EUROCODE 3 CHECK (EN 1993-1-1)")
        lines.append("==============================")

        if HAS_PRETTYTABLE:
            # Table 0: Section & Material Properties
            t0 = PrettyTable()
            t0.title = "Section & Material Properties"
            t0.field_names = ["Property", "Value", "Unit", "Property ", "Value ", "Unit "]

            def fmt(val, prec=1):
                return f"{val:.{prec}f}"

            t0.add_row(["fy", fmt(self.fy / 1e6, 1), "MPa", "E", fmt(self.E / 1e9, 1), "GPa"])
            t0.add_row(["h", fmt(self.h * 1000, 1), "mm", "b", fmt(self.b * 1000, 1), "mm"])
            t0.add_row(["tw", fmt(self.tw * 1000, 1), "mm", "tf", fmt(self.tf * 1000, 1), "mm"])
            t0.add_row(["A", fmt(self.A * 1e4, 2), "cm2", "L", fmt(self.L, 2), "m"])
            t0.add_row(["Iy", fmt(self.Iy * 1e8, 1), "cm4", "Iz", fmt(self.Iz * 1e8, 1), "cm4"])
            t0.add_row(["Wel,y", fmt(self.Wel_y * 1e6, 1), "cm3", "Wel,z", fmt(self.Wel_z * 1e6, 1), "cm3"])
            t0.add_row(["Wpl,y", fmt(self.Wpl_y * 1e6, 1), "cm3", "Wpl,z", fmt(self.Wpl_z * 1e6, 1), "cm3"])
            t0.add_row(["It", fmt(self.It * 1e8, 2), "cm4", "Iw", fmt(self.Iw * 1e12, 2), "cm6"])

            lines.append(str(t0))
            lines.append("")

            t1 = PrettyTable()
            t1.title = f"Critical Check at x={c.get('pos', 0):.2f}m"
            t1.field_names = ["Force", "Design (Ed)", "Resist (Rd)", "UC"]

            def row(n, ed, rd, u=""):
                return [n, f"{abs(ed) / 1000:.1f} {u}", f"{rd / 1000:.1f} {u}", f"{abs(ed) / rd if rd else 0:.2f}"]

            t1.add_row(row("N_Ed", c.get('Ned', 0), c.get('Nc_Rd', 0), "kN"))
            t1.add_row(row("My_Ed", c.get('My', 0), c.get('Mc_Rd_y', 0), "kNm"))
            t1.add_row(row("Mz_Ed", c.get('Mz', 0), c.get('Mc_Rd_z', 0), "kNm"))
            t1.add_row(row("Vy_Ed", c.get('Vy', 0), c.get('Vpl_Rd_y', 0), "kN"))
            t1.add_row(row("Vz_Ed", c.get('Vz', 0), c.get('Vpl_Rd_z', 0), "kN"))
            lines.append(str(t1))
            lines.append("")

        lines.append("CALCULATION DETAILS")
        lines.append("-------------------")
        lines.append(f"1. GEOMETRY & CLASSIFICATION")
        lines.append(f"   Section: {self.section_type}")
        lines.append(f"   Class: {s_class} (Epsilon={self.epsilon:.3f})")
        lines.append(f"   Modulus used: Wy={c.get('W_y', 0) * 1e6:.1f} cm3,     Wz={c.get('W_z', 0) * 1e6:.1f} cm3")
        lines.append(f"   Modulus used: Wy={c.get('W_y', 0) * 1e6:.1f} cm3,     Wz={c.get('W_z', 0) * 1e6:.1f} cm3")
        lines.append(f"2. BEAM RESISTANCE")
        lines.append(f"   Beam axial resistance         Nc_Rd={c.get('Nc_Rd', 0) * 1e-3:.1f} kN" )
        lines.append(f"   Beam shear y resistance       Vpl_Rd_y={c.get('Vpl_Rd_y', 0) * 1e-3:.1f} kN")
        lines.append(f"   Beam shear z resistance       Vpl_Rd_z={c.get('Vpl_Rd_z', 0) * 1e-3:.1f} kN")
        lines.append(f"   Beam flexure IP resistance    Mc_Rd_y={c.get('Mc_Rd_y', 0) * 1e-3:.1f} kN*m" )
        lines.append(f"   Beam flexure OP resistance    Mc_Rd_z={c.get('Mc_Rd_z', 0) * 1e-3:.1f} kN*m" )
        lines.append(f"   Beam Torsion resistance       T_Rd={c.get('T_Rd', 0) * 1e-3:.1f} kN*m" )
        lines.append(f"\n2. FLEXURAL BUCKLING (Major Axis Y-Y)")
        lines.append(f"   Lcr,y = {Lcr_y:.2f} m")
        lines.append(f"   Ncr,y = (pi^2 * E * Iy) / Lcr^2 = {c.get('Ncr_y', 0) / 1000:.1f} kN")
        lines.append(f"   Lambda_y = sqrt(A*fy / Ncr) = {c.get('lambda_y', 0):.3f}")
        lines.append(f"   Curve: {self.parameters.get('Buckling_curve_y', 'a')} -> Chi_y = {c.get('chi_y', 0):.3f}")
        lines.append(f"   Nb,Rd,y = Chi * A * fy / gM1 = {c.get('Nb_Rd_y', 0) / 1000:.1f} kN")

        lines.append(f"\n3. FLEXURAL BUCKLING (Minor Axis Z-Z)")
        lines.append(f"   Lcr,z = {Lcr_z:.2f} m")
        lines.append(f"   Ncr,z = {c.get('Ncr_z', 0) / 1000:.1f} kN")
        lines.append(f"   Lambda_z = {c.get('lambda_z', 0):.3f}")
        lines.append(f"   Curve: {self.parameters.get('Buckling_curve_z', 'b')} -> Chi_z = {c.get('chi_z', 0):.3f}")
        lines.append(f"   Nb,Rd,z = {c.get('Nb_Rd_z', 0) / 1000:.1f} kN")

        lines.append(f"\n4. LATERAL TORSIONAL BUCKLING")
        lines.append(f"   Mcr = {c.get('Mcr', 0) / 1000:.1f} kNm")
        lines.append(f"   Lambda_LT = sqrt(Wy*fy / Mcr) = {c.get('lambda_LT', 0):.3f}")
        lines.append(f"   Curve: {self.parameters.get('LTB_curve', 'a')} -> Chi_LT = {c.get('chi_LT', 0):.3f}")
        lines.append(f"   Mb,Rd = Chi_LT * Wy * fy / gM1 = {c.get('Mb_Rd', 0) / 1000:.1f} kNm")

        lines.append(f"\n5. INTERACTION FACTORS (Method 2)")
        lines.append(f"   kyy = {c.get('kyy', 0):.3f}")
        lines.append(f"   kzz = {c.get('kzz', 0):.3f}")
        lines.append(f"   kyz = {c.get('kyz', 0):.3f}")
        lines.append(f"   kzy = {c.get('kzy', 0):.3f}")

        lines.append(f"\n6. FINAL UTILITY CHECKS")
        lines.append(f"   Eq 6.61 (Major+LTB): N/Nb_y + kyy*(My/Mb_Rd) + kyz*(Mz/Mc_z)")
        lines.append(
            f"      -> {abs(c.get('Ned', 0)) / c.get('Nb_Rd_y', 1):.2f} + {c.get('kyy', 0):.2f}*{c.get('My', 0) / c.get('Mb_Rd', 1):.2f} + {c.get('kyz', 0):.2f}*{c.get('Mz', 0) / c.get('Mc_Rd_z', 1):.2f}")
        lines.append(f"      = {c.get('uc_stab_661', 0):.3f}")

        lines.append(f"   Eq 6.62 (Minor):     N/Nb_z + kzy*(My/Mb_Rd) + kzz*(Mz/Mc_z)")
        lines.append(
            f"      -> {abs(c.get('Ned', 0)) / c.get('Nb_Rd_z', 1):.2f} + {c.get('kzy', 0):.2f}*{c.get('My', 0) / c.get('Mb_Rd', 1):.2f} + {c.get('kzz', 0):.2f}*{c.get('Mz', 0) / c.get('Mc_Rd_z', 1):.2f}")
        lines.append(f"      = {c.get('uc_stab_662', 0):.3f}")

        lines.append(f"\n   MAX UC: {max_uc:.3f}")

        return "\n".join(lines)

    def _classify_section_geometry(self):
        eps = self.epsilon
        if self.d > 0 and self.t > 0:
            dt = self.d / self.t
            if dt <= 50 * eps ** 2: return 1
            if dt <= 70 * eps ** 2: return 2
            if dt <= 90 * eps ** 2: return 3
            return 4
        elif self.b > 0 and self.tw == self.tf and self.tw > 0:
            c = self.b - 3 * self.tw
            ct = c / self.tw
            if ct <= 33 * eps: return 1
            if ct <= 38 * eps: return 2
            if ct <= 42 * eps: return 3
            return 4
        elif self.h > 0 and self.tw > 0 and self.tf > 0:
            c_flange = (self.b / 2) - (self.tw / 2)
            ct_flange = c_flange / self.tf
            c_web = self.h - 2 * self.tf
            ct_web = c_web / self.tw
            f_class = 4
            if ct_flange <= 9 * eps:
                f_class = 1
            elif ct_flange <= 10 * eps:
                f_class = 2
            elif ct_flange <= 14 * eps:
                f_class = 3
            w_class = 4
            if ct_web <= 72 * eps:
                w_class = 1
            elif ct_web <= 83 * eps:
                w_class = 2
            elif ct_web <= 124 * eps:
                w_class = 3
            return max(f_class, w_class)
        return 3

    def _get_chi(self, lam, curve):
        alphas = {'a0': 0.13, 'a': 0.21, 'b': 0.34, 'c': 0.49, 'd': 0.76}
        alpha = alphas.get(curve, 0.34)
        phi = 0.5 * (1 + alpha * (lam - 0.2) + lam ** 2)
        if phi ** 2 < lam ** 2: return 1.0
        chi = 1 / (phi + math.sqrt(phi ** 2 - lam ** 2))
        return min(chi, 1.0)

    def _get_chi_LT(self, lam_LT, curve):
        alphas = {'a': 0.21, 'b': 0.34, 'c': 0.49, 'd': 0.76}
        alpha = alphas.get(curve, 0.21)
        phi_LT = 0.5 * (1 + alpha * (lam_LT - 0.2) + lam_LT ** 2)
        if phi_LT ** 2 < lam_LT ** 2: return 1.0
        chi_LT = 1 / (phi_LT + math.sqrt(phi_LT ** 2 - lam_LT ** 2))
        return min(chi_LT, 1.0)


StandardsRegistry.register(Eurocode3Standard)