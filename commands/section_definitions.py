import math

NBSEGMENTS = 6  # Increased for smoother rounds


def get_section_points(section_type, length, params):
    """Returns points and faces for different section types"""
    points = []
    faces = []
    # Detect Geometry Type for "Tubular-Shape" (merged CHS and HSS)
    geometry_type = section_type
    if section_type == "Tubular-Shape":
        # If 'd' (Diameter) exists in params, treat as CHS/Round
        if 'd' in params:
            geometry_type = "CHS"
        # If profile name starts with CHS
        elif params.get("_StandardSectionName", "").startswith("CHS"):
            geometry_type = "CHS"
        else:
            # Default to HSS/Rectangular for SHS/HSS/RHS
            geometry_type = "HSS"

    # Generate Geometry Points based on Type
    if section_type in ["I-Shape", "H-Shape", "Asymmetric I-Shape"]:
        points = create_I_section(section_type, params, length=0)
        points += create_I_section(section_type, params, length=length)
        faces = [
            # Bottom flange
            [0, 1, 2, 3, -1, 12, 13, 14, 15, -1],
            # Web
            [4, 5, 6, 7, -1, 16, 17, 18, 19, -1],
            # Top flange
            [8, 9, 10, 11, -1, 20, 21, 22, 23, -1],
            # Left side
            [0, 3, 15, 12, -1, 3, 4, 16, 15, -1,
             4, 16, 19, 7, -1, 7, 8, 20, 19, -1,
             8, 11, 23, 20, -1],
            # Right side
            [1, 13, 14, 2, -1, 2, 14, 17, 5, -1,
             5, 17, 18, 6, -1, 6, 18, 21, 9, -1,
             9, 21, 22, 10, -1],
            # Caps
            [0, 12, 13, 1, -1, 11, 23, 22, 10, -1]
        ]

    elif section_type == "Rectangle":
        points = create_Rectangle_section(section_type, params, length=0)
        points += create_Rectangle_section(section_type, params, length=length)
        faces = [
            [0, 1, 2, 3, -1],  # Start face
            [4, 5, 6, 7, -1],  # End face
            [0, 1, 5, 4, -1],  # Bottom face
            [1, 2, 6, 5, -1],  # Right face
            [2, 3, 7, 6, -1],  # Top face
            [3, 0, 4, 7, -1]  # Left face
        ]
    elif section_type == "L-Shape":
        points = create_L_section(section_type, params, length=0)
        points += create_L_section(section_type, params, length=length)

        faces = [
            # Web faces
            [0, 1, 2, 3, -1, 7, 8, 9, 10, -1],  # Vertical leg
            [0, 6, 5, 4, 3, -1, 7, 13, 12, 11, 10, -1],  # Horizontal leg

            # Connection faces
            [3, 4, 11, 10, -1],
            [1, 8, 9, 2, -1],
            [2, 9, 13, 6, -1],
            [4, 5, 12, 11, -1],
            [5, 6, 13, 12, -1],
            [0, 3, 10, 7, -1],

            # End caps
            [0, 1, 8, 7, -1],
            [5, 6, 13, 12, -1]
        ]
    elif section_type in ["C-Shape", "U-Shape"]:
        points = create_U_section(section_type, params, length=0)
        points += create_U_section(section_type, params, length=length)
        faces = [
            # Web
            [0, 1, 11, 10, -1],
            # Flanges
            [1, 2, 12, 11, -1],
            [3, 4, 14, 13, -1],
            # Lips
            [5, 6, 16, 15, -1],
            [7, 8, 18, 17, -1],
            # Connections
            [2, 3, 13, 12, -1],
            [6, 7, 17, 16, -1],
            [0, 10, 13, 3, -1],
            [0, 1, 2, 3, -1],
            [10, 11, 12, 13, -1],
            [1, 9, 8, 7, -1],
            [6, 5, 4, 2, -1],
            [11, 19, 18, 17, -1],
            [16, 15, 14, 12, -1],
            # End caps
            [0, 9, 19, 10, -1],
            [4, 5, 15, 14, -1],
            [8, 9, 19, 18, -1]
        ]
    elif section_type in ["T-Shape"]:
        points = create_T_section(section_type, params, length=0)
        points += create_T_section(section_type, params, length=length)
        faces = [
            # Web
            [0, 1, 2, 3, -1, 8, 9, 10, 11, -1],
            # Top flange
            [4, 5, 6, 7, -1, 12, 13, 14, 15, -1],
            # Left side
            [0, 8, 11, 3, -1, 4, 3, 11, 12, -1, 4, 12, 15, 7, -1],
            # Right side
            [1, 9, 10, 2, -1, 2, 5, 13, 10, -1, 5, 13, 14, 6, -1],
            # Caps
            [0, 1, 8, 9, -1, 7, 6, 14, 15, -1]
        ]
    elif section_type in ["Round Bar"]:
        points = create_round_section(section_type, params, length=0)
        points += create_round_section(section_type, params, length=length)
        faces = create_round_faces(section_type, params)
    elif section_type in ["CHS", "Tubular"]:
        points = create_chs_section(section_type, params, length=0)
        points += create_chs_section(section_type, params, length=length)
        faces = create_chs_faces(params)
    elif section_type == "HSS":
        points = create_Rectangle_section(section_type, params, length=0)
        points += create_Rectangle_section(section_type, params, length=length)
        faces = [
            [0, 1, 2, 3, -1], [4, 5, 6, 7, -1],
            [0, 1, 5, 4, -1], [1, 2, 6, 5, -1],
            [2, 3, 7, 6, -1], [3, 0, 4, 7, -1]
        ]

    # Calculate Properties
    # We pass the half-points (cross-section only) to the calculator
    props = calculate_section_properties(section_type, points[:len(points) // 2], params)

    # Calculate centroid (COG) and offset points to center on it
    # Note: Round/CHS are usually generated centered already, others might not be
    if section_type not in ["Round Bar", "CHS", "Tubular"]:
        cog_y, cog_z = props['centroid']

        # Offset all points to center on COG
        offset_points = []
        for x, y, z in points:
            offset_points.append((x, y - cog_y, z - cog_z))
        points = offset_points

    return points, faces, props


def create_round_section(section_type, params, length=0):
    """Create points for round bar or tubular section"""
    diameter = params.get('Width', params.get('d', 0))
    segments = NBSEGMENTS

    points = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = length
        y = (diameter / 2) * math.cos(angle)
        z = (diameter / 2) * math.sin(angle)
        points.append((x, y, z))
    return points


def create_round_faces(section_type, params):
    """Create faces for round bar"""
    segments = NBSEGMENTS
    faces = []

    # Start face
    start_face = list(range(segments))
    start_face.append(-1)
    faces.append(start_face)

    # End face
    end_face = list(range(segments, 2 * segments))
    end_face.append(-1)
    faces.append(end_face)

    # Side faces (triangles)
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([
            i, next_i, next_i + segments, i + segments, -1
        ])
    return faces


def create_chs_section(section_type, params, length=0):
    """Create points for circular hollow section (CHS)"""
    diameter = params.get('Width', params.get('d', 0))
    thickness = params.get('Thickness', params.get('t', 0))
    segments = NBSEGMENTS

    points = []
    # Outer circle
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = length
        y = (diameter / 2) * math.cos(angle)
        z = (diameter / 2) * math.sin(angle)
        points.append((x, y, z))

    # Inner circle
    inner_diameter = diameter - 2 * thickness
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = length
        y = (inner_diameter / 2) * math.cos(-angle)
        z = (inner_diameter / 2) * math.sin(-angle)
        points.append((x, y, z))

    return points


def create_chs_faces(params):
    segments = NBSEGMENTS
    faces = []
    outer_start = list(range(segments))
    outer_start.append(-1)
    faces.append(outer_start)
    outer_end = list(range(segments, 2 * segments))
    outer_end.append(-1)
    faces.append(outer_end)
    inner_start = list(range(2 * segments, 3 * segments))
    inner_start.append(-1)
    faces.append(inner_start)
    inner_end = list(range(3 * segments, 4 * segments))
    inner_end.append(-1)
    faces.append(inner_end)

    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([i, next_i, next_i + segments, i + segments, -1])

    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([i + 2 * segments, next_i + 2 * segments, next_i + 3 * segments, i + 3 * segments, -1])

    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([i, i + 2 * segments, next_i + 2 * segments, next_i, -1])
        faces.append([i + segments, i + 3 * segments, next_i + 3 * segments, next_i + segments, -1])
    return faces


def create_I_section(section_type, params, length=0):
    h = params.get('Height', params.get('h', 0))
    tw = params.get('WebThickness', params.get('tw', 0))

    if section_type == "Asymmetric I-Shape":
        w_top = params['TopFlangeWidth']
        w_bottom = params['BottomFlangeWidth']
        tf_top = params['TopFlangeThickness']
        tf_bottom = params['BottomFlangeThickness']
    else:
        w = params.get('Width', params.get('b', 0))
        tf = params.get('FlangeThickness', params.get('tf', 0))
        w_top = w_bottom = w
        tf_top = tf_bottom = tf

    top = h / 2
    bottom = -h / 2
    web_left = -tw / 2
    web_right = tw / 2
    top_flange_bottom = top - tf_top
    top_left = -w_top / 2
    top_right = w_top / 2
    bottom_flange_top = bottom + tf_bottom
    bottom_left = -w_bottom / 2
    bottom_right = w_bottom / 2

    points = [
        (length, bottom_left, bottom),
        (length, bottom_right, bottom),
        (length, bottom_right, bottom_flange_top),
        (length, bottom_left, bottom_flange_top),
        (length, web_left, bottom_flange_top),
        (length, web_right, bottom_flange_top),
        (length, web_right, top_flange_bottom),
        (length, web_left, top_flange_bottom),
        (length, top_left, top_flange_bottom),
        (length, top_right, top_flange_bottom),
        (length, top_right, top),
        (length, top_left, top),
    ]
    return points


def create_Rectangle_section(section_type, params, length=0):
    w = params.get('Width', params.get('b', 0))
    h = params.get('Height', params.get('h', 0))
    left = -w / 2
    right = w / 2
    bottom = -h / 2
    top = h / 2

    points = [
        (length, left, bottom),
        (length, right, bottom),
        (length, right, top),
        (length, left, top),
    ]
    return points


def create_L_section(section_type, params, length=0):
    leg1 = params.get('Width', params.get('b', 0))
    leg2 = params.get('Height', params.get('h', 0))
    thickness = params.get('Thickness', params.get('t', 0))

    points = [
        (length, -thickness / 2, thickness / 2),
        (length, leg1 - thickness / 2, thickness / 2),
        (length, leg1 - thickness / 2, -thickness / 2),
        (length, -thickness / 2, -thickness / 2),
        (length, -thickness / 2, -leg2 + thickness / 2),
        (length, thickness / 2, -leg2 + thickness / 2),
        (length, thickness / 2, -thickness / 2)
    ]
    return points


def create_U_section(section_type, params, length=0):
    h = params.get('Height', params.get('h', 0))
    w = params.get('Width', params.get('b', 0))
    t = params.get('Thickness', params.get('tw', 0))
    if t == 0: t = params.get('t', 0)

    left = -w / 2
    right = w / 2
    bottom = -h / 2
    top = h / 2

    points = [
        (length, left, bottom), (length, left + t, bottom),
        (length, left + t, top), (length, left, top),
        (length, right, top), (length, right, top - t),
        (length, left + t, top - t), (length, left + t, bottom + t),
        (length, right, bottom + t), (length, right, bottom)
    ]
    return points


def create_T_section(section_type, params, length=0):
    h = params.get('Height', params.get('h', 0))
    tw = params.get('WebThickness', params.get('tw', 0))
    w = params.get('Width', params.get('b', 0))
    tf = params.get('FlangeThickness', params.get('tf', 0))

    top = h / 2
    bottom = -h / 2
    web_left = -tw / 2
    web_right = tw / 2
    top_flange_bottom = top - tf
    top_left = -w / 2
    top_right = w / 2

    points = [
        (length, web_left, bottom),
        (length, web_right, bottom),
        (length, web_right, top_flange_bottom),
        (length, web_left, top_flange_bottom),
        (length, top_left, top_flange_bottom),
        (length, top_right, top_flange_bottom),
        (length, top_right, top),
        (length, top_left, top),
    ]
    return points


def organize_points_by_beam_type(section_type, points):
    points_2d = [(round(y, 6), round(z, 6)) for (x, y, z) in points]
    ordered_points = []

    if section_type in ["I-Shape", "H-Shape", "Asymmetric I-Shape"]:
        if len(points_2d) == 12:
            ordered_points = [
                points_2d[0], points_2d[1], points_2d[2], points_2d[5],
                points_2d[6], points_2d[9], points_2d[10], points_2d[11],
                points_2d[8], points_2d[7], points_2d[4], points_2d[3],
                points_2d[0]
            ]
    elif section_type == "Rectangle":
        if len(points_2d) == 4:
            ordered_points = [
                points_2d[0], points_2d[1], points_2d[2], points_2d[3],
                points_2d[0]
            ]
    elif section_type == "L-Shape":
        if len(points_2d) == 7:
            ordered_points = [
                points_2d[0], points_2d[1], points_2d[2], points_2d[6],
                points_2d[5], points_2d[4], points_2d[3],
                points_2d[0]
            ]
    elif section_type in ["C-Shape", "U-Shape"]:
        if len(points_2d) == 10:
            ordered_points = [
                points_2d[0], points_2d[1], points_2d[9], points_2d[8],
                points_2d[7], points_2d[6], points_2d[5], points_2d[4],
                points_2d[2], points_2d[3], points_2d[0],
            ]
    elif section_type in ["T-Shape"]:
        if len(points_2d) == 8:
            ordered_points = [
                points_2d[0], points_2d[1], points_2d[2], points_2d[5],
                points_2d[6], points_2d[7], points_2d[4], points_2d[3],
                points_2d[0]
            ]
    return ordered_points


def calculate_section_properties(section_type, points, params=None):
    """
    Calculate section properties based on points or standard formulas.
    Returns: Dict with area, Iy, Iz, Wel_y, Wel_z, Wpl_y, Wpl_z, etc.
    """
    props = zero_properties()

    # 1. SPECIAL CASES: Analytical Formulas (Round/Tube/HSS)
    if params and section_type in ["CHS", "Tubular", "Round Bar", "HSS"]:
        if section_type in ["CHS", "Tubular"]:
            props = calculate_chs_section_properties(params)
        elif section_type == "Round Bar":
            props = calculate_round_section_properties(params)
        elif section_type == "HSS":
            props = calculate_hss_section_properties(params)

    # 2. GENERAL CASES: Geometric Calculation (Polygon)
    else:
        ordered_points = organize_points_by_beam_type(section_type, points)
        props = calculate_polygon_properties_from_ordered_points(ordered_points)
    # 3. PLASTIC PROPERTIES (Calculated from formulas/geometry)
    # If not already computed (e.g. by polygon generic logic which doesn't do Wpl yet),
    # we compute Wpl here using the dimensions.
    if params:
        pl_props = calculate_plastic_properties(section_type, params, props['centroid'])
        props.update(pl_props)

    # 4. OVERRIDES: Standard Library Values
    # If standard parameters are provided (e.g., from Eurocode DB), use them.
    if params:
        # Standard Area and Inertia
        if "A" in params: props['area'] = float(params['A'])
        if "Iy" in params: props['Iy'] = float(params['Iy'])
        if "Iz" in params: props['Iz'] = float(params['Iz'])
        if "Iw" in params: props['Iw'] = float(params['Iw'])
        if "It" in params: props['J'] = float(params['It'])
        if "Wel_y" in params:
            props['Wel_y'] = float(params["Wel_y"])
        if "Wel_z" in params:
            props['Wel_z'] = float(params["Wel_z"])
        # Standard Plastic Modulus
        if "Wpl_y" in params:
            props['Wpl_y'] = float(params["Wpl_y"])
        if "Wpl_z" in params:
            props['Wpl_z'] = float(params["Wpl_z"])

    return props


def calculate_plastic_properties(section_type, params, centroid):
    """
    Calculates Plastic Moduli (Wpl_y, Wpl_z) using standard formulas.
    """
    h = params.get('Height', params.get('h', 0.0))
    b = params.get('Width', params.get('b', 0.0))
    tw = params.get('WebThickness', params.get('tw', 0.0))
    tf = params.get('FlangeThickness', params.get('tf', 0.0))

    # Check for simplified thickness 't' if tw/tf not set
    if tw == 0 and tf == 0:
        t = params.get('Thickness', params.get('t', 0.0))
        tw = tf = t

    Wpl_y = 0.0
    Wpl_z = 0.0

    if section_type in ["I-Shape", "H-Shape", "Asymmetric I-Shape"]:
        # Doubly Symmetric I-section formulas
        # Wpl_y (Major) = web_plastic + flanges_plastic
        # Wpl_y = (tw * (h - 2*tf)^2) / 4 + b * tf * (h - tf)
        Wpl_y = (tw * (h - 2 * tf) ** 2) / 4.0 + b * tf * (h - tf)

        # Wpl_z (Minor) = 2 * (tf * b^2)/4 + (h - 2*tf)*tw^2 / 4
        Wpl_z = (2 * tf * b ** 2) / 4.0 + ((h - 2 * tf) * tw ** 2) / 4.0

    elif section_type == "Rectangle":
        Wpl_y = (b * h ** 2) / 4.0
        Wpl_z = (h * b ** 2) / 4.0

    elif section_type in ["Round Bar"]:
        d = b
        Wpl_y = (d ** 3) / 6.0
        Wpl_z = Wpl_y

    elif section_type in ["CHS", "Tubular"]:
        d = b
        t = params.get('Thickness', params.get('t', 0.0))
        di = d - 2 * t
        if di > 0:
            Wpl_y = (d ** 3 - di ** 3) / 6.0
            Wpl_z = Wpl_y

    elif section_type == "HSS":
        # Box Section: Outer Rectangle - Inner Rectangle
        t = params.get('Thickness', params.get('t', 0.0))
        bi = b - 2 * t
        hi = h - 2 * t
        if bi > 0 and hi > 0:
            Wpl_y = (b * h ** 2 / 4.0) - (bi * hi ** 2 / 4.0)
            Wpl_z = (h * b ** 2 / 4.0) - (hi * bi ** 2 / 4.0)

    elif section_type in ["C-Shape", "U-Shape"]:
        # Approximation or composite rectangle calc
        # Standard U-shape (flanges vertical)
        # We assume standard orientation: Web along Y? No, Web along Z usually for C-channel major.
        # Let's assume U-Shape defined as: Web height h, Flange width b.
        # Wpl_y (Major axis, perp to web):
        # A_total = 2*b*tf + (h-2*tf)*tw
        # PNA calculation is required for exact.
        # Fallback to Shape Factor ~ 1.15 for now if exact formula too complex for snippet
        # Or implement basic Plastic Neutral Axis finder:
        parts = [
            {'b': b, 'h': tf, 'y': 0, 'z': h / 2 - tf / 2},  # Top Flange
            {'b': b, 'h': tf, 'y': 0, 'z': -h / 2 + tf / 2},  # Bot Flange
            {'b': tw, 'h': h - 2 * tf, 'y': -b / 2 + tw / 2, 'z': 0}  # Web (left aligned)
        ]
        # Note: Position logic depends on how `create_U_section` centers them.
        # If too complex, we return 0 and rely on elastic * 1.15 in calling code
        pass

    return {'Wpl_y': Wpl_y, 'Wpl_z': Wpl_z}


def calculate_hss_section_properties(params):
    b = params.get('Width', params.get('b', 0))
    h = params.get('Height', params.get('h', 0))
    t = params.get('Thickness', params.get('t', 0))

    if t <= 0 or t >= min(b, h) / 2:
        return zero_properties()

    bi = b - 2 * t
    hi = h - 2 * t

    area = (b * h) - (bi * hi)
    Iy = (b * h ** 3 - bi * hi ** 3) / 12
    Iz = (h * b ** 3 - hi * bi ** 3) / 12

    # Elastic Modulus
    Wel_y = Iy / (h / 2)
    Wel_z = Iz / (b / 2)

    # Plastic Modulus
    Wpl_y = (b * h ** 2 - bi * hi ** 2) / 4
    Wpl_z = (h * b ** 2 - hi * bi ** 2) / 4

    return {
        'area': area,
        'Iy': Iy, 'Iz': Iz, 'Iyz': 0,
        'centroid': (0, 0),
        'Wel_y': Wel_y, 'Wel_z': Wel_z,
        'Wpl_y': Wpl_y, 'Wpl_z': Wpl_z
    }


def calculate_round_section_properties(params):
    diameter = params.get('Width', params.get('d', 0))
    radius = diameter / 2
    area = math.pi * radius ** 2
    Iy = (math.pi * diameter ** 4) / 64
    Iz = Iy

    # Elastic Modulus
    Wel = Iy / radius
    # Plastic Modulus
    Wpl = (diameter ** 3) / 6.0

    return {
        'area': area,
        'Iy': Iy, 'Iz': Iz, 'Iyz': 0,
        'centroid': (0, 0),
        'Wel_y': Wel, 'Wel_z': Wel,
        'Wpl_y': Wpl, 'Wpl_z': Wpl
    }


def calculate_chs_section_properties(params):
    diameter = params.get('Width', params.get('d', 0))
    thickness = params.get('Thickness', params.get('t', 0))
    radius = diameter / 2
    inner_diameter = diameter - 2 * thickness

    if inner_diameter <= 0: return zero_properties()

    inner_radius = inner_diameter / 2
    area = math.pi * (radius ** 2 - inner_radius ** 2)
    Iy = (math.pi / 64) * (diameter ** 4 - inner_diameter ** 4)
    Iz = Iy

    Wel = Iy / radius
    Wpl = (diameter ** 3 - inner_diameter ** 3) / 6.0

    return {
        'area': area,
        'Iy': Iy, 'Iz': Iz, 'Iyz': 0,
        'centroid': (0, 0),
        'Wel_y': Wel, 'Wel_z': Wel,
        'Wpl_y': Wpl, 'Wpl_z': Wpl
    }


def calculate_polygon_properties_from_ordered_points(ordered_points):
    if not ordered_points:
        return zero_properties()

    area = 0.0
    centroid_y = 0.0
    centroid_z = 0.0
    Ix_gross = 0.0  # I about z-axis (FreeCAD Iy)
    Iy_gross = 0.0  # I about y-axis (FreeCAD Iz)
    Iyz_gross = 0.0

    n = len(ordered_points)
    for i in range(n - 1):
        yi, zi = ordered_points[i]
        yj, zj = ordered_points[i + 1]
        cross = yi * zj - yj * zi
        area += cross
        centroid_y += (yi + yj) * cross
        centroid_z += (zi + zj) * cross
        Iy_gross += (yi ** 2 + yi * yj + yj ** 2) * cross
        Ix_gross += (zi ** 2 + zi * zj + zj ** 2) * cross
        Iyz_gross += (yi * zj + 2 * yi * zi + 2 * yj * zj + yj * zi) * cross

    area *= 0.5
    if area == 0: return zero_properties()

    centroid_y /= (6 * area)
    centroid_z /= (6 * area)

    Iy_gross /= 12
    Ix_gross /= 12
    Iyz_gross /= 24

    # Parallel axis theorem
    # Iy -> Inertia about Major Axis (usually horizontal in standard engineering, but FreeCAD Z is height)
    # FreeCAD Convention:
    #   Iyy = Integral z^2 dA (Bending about Y axis) -> Corresponds to Ix_gross
    #   Izz = Integral y^2 dA (Bending about Z axis) -> Corresponds to Iy_gross

    Iyy = Ix_gross - area * centroid_z ** 2
    Izz = Iy_gross - area * centroid_y ** 2
    Iyz = Iyz_gross - area * centroid_y * centroid_z

    # Section Moduli (Elastic)
    # Wel_y = Iyy / z_max
    z_coords = [z for (y, z) in ordered_points]
    max_z = max(z_coords) - centroid_z
    min_z = centroid_z - min(z_coords)

    Wel_y = 0
    if max_z > 0 and min_z > 0:
        Wel_y = min(Iyy / max_z, Iyy / min_z)

    y_coords = [y for (y, z) in ordered_points]
    max_y = max(y_coords) - centroid_y
    min_y = centroid_y - min(y_coords)

    Wel_z = 0
    if max_y > 0 and min_y > 0:
        Wel_z = min(Izz / max_y, Izz / min_y)

    return {
        'area': abs(area),
        'Iy': abs(Iyy),
        'Iz': abs(Izz),
        'Iyz': Iyz,
        'centroid': (centroid_y, centroid_z),
        'Wel_y': Wel_y,
        'Wel_z': Wel_z,
        'Wpl_y': 0.0,  # Placeholder, will be calculated by plastic func or shape factor
        'Wpl_z': 0.0
    }


def zero_properties():
    return {
        'area': 0, 'Iy': 0, 'Iz': 0, 'Iyz': 0,
        'centroid': (0, 0),
        'Wel_y': 0, 'Wel_z': 0,
        'Wpl_y': 0, 'Wpl_z': 0
    }